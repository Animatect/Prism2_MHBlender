import os
import sys
import threading
import platform
import traceback
import time
import shutil
import logging
import operator
import tempfile
import math
import mathutils

import bpy

from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *

if eval(os.getenv("PRISM_DEBUG", "False")):
    try:
        del sys.modules["widget_import_scenedata"]
    except:
        pass

import widget_import_scenedata
from PrismUtils.Decorators import err_catcher as err_catcher

logger = logging.getLogger(__name__)

class Prism_BlenderMHExtension_Functions(object):
    def __init__(self, core, plugin):
        self.core = core
        self.plugin = plugin
        self.blenderplugin = self.core.appPlugin
        self.AOVDict = self.lowercaseAOVdict({
"ambient occlusion":"AO",
"cryptomatte asset":"CryptoAsset",
"cryptomatte material":"CryptoMaterial",
"cryptomatte object":"CryptoObject",
"diffuse color":"DiffCol",
"diffuse direct":"DiffDir",
"diffuse indirect":"DiffInd",
"emission":"Emit",
"environment":"Env",
"glossy color":"GlossCol",
"glossy direct":"GlossDir",
"glossy indirect":"GlossInd",
"material index":"IndexMA",
"mist":"Mist",
"normal":"Normal",
"object index":"IndexOB",
"position":"Position",
"transmission color":"TransCol",
"transmission direct":"TransDir",
"transmission indirect":"TransInd",
"uv":"UV",
"vector":"Vector",
"z":"Depth",
"denoising data": "Denoising",
"debug samples":"Debug Sample Count",
"shadow catcher":"Shadow Catcher",
"volume direct":"VolumeDir",
"volume indirect":"VolumeInd",
"bloom":"BloomCol",
"transparent":"Transp",

})
        self.layerProperties = {
            "Environment":"use_sky",
            "Surfaces":"use_solid",
            "Curves":"use_strand",
            "Volumes":"use_volumes",
            "Motion Blur":"use_motion_blur",
            "Denoising":"cycles.use_denoising",
        }

        self.core.registerCallback("onStateDeleted", self.onStateDeleted, plugin=self)
    
    @err_catcher(name=__name__)
    def isUsingCycles(self)->bool:
        return bpy.context.scene.render.engine == 'CYCLES'
    @err_catcher(name=__name__)
    def isUsingEevee(self)->bool:
        return bpy.context.scene.render.engine == 'BLENDER_EEVEE'


    @err_catcher(name=__name__)
    def lowercaseAOVdict(self, original_dict:dict)->dict:
        lowercase_dict = {key.lower(): value for key, value in original_dict.items()}
        return lowercase_dict

    @err_catcher(name=__name__)
    def startup(self):
        pass
        
    # Create a new view layer
    @err_catcher(name=__name__)
    def createViewLayer(self, layername):
        new_layer_name = layername
        bpy.context.scene.view_layers.new(name=new_layer_name)

    ##############################
    #                            #
    ####### MH REND LAYER ########
    #                            #
    ##############################
    @err_catcher(name=__name__)
    def getRenderLayers(self):
        scene = bpy.context.scene
        layers = [view_layer.name for view_layer in scene.view_layers]
        return layers
    
    @err_catcher(name=__name__)
    def sm_render_getRenderPasses(self, origin, layername):
        # Return the render passes if the render passes are not active, 
        # or in other words, return remaining render passes.
        aovNames = [
            x["name"]
            for x in self.getAvailableAOVs(layername)
            if x["name"] not in self.getViewLayerAOVs(layername)
        ]
        return aovNames
    
    @err_catcher(name=__name__)
    def sm_render_refreshPasses(self, origin):
        origin.lw_passes.clear()
        
        self.blenderplugin.canDeleteRenderPasses = True
        passNames = self.getViewLayerAOVs(origin.cb_renderLayer.currentText())
        logger.debug("viewlayer aovs: %s" % passNames)

        tech = []
        main = []
        crypto = []
        for i in sorted(passNames, key=lambda s: s.lower()):
            passname:str = self.AOVDict[i.lower()]
            if self.compareTechPass(passname):
                tech.append(i)
            elif 'crypto' in passname.lower():
                crypto.append(i)
            else:
                main.append(i)
        passNames = tech + main + crypto

        origin.lw_passes.addItems(passNames)
        for index in range(origin.lw_passes.count()):
            item = origin.lw_passes.item(index)
            i = item.text()
            if i in tech:
                item.setBackground(QColor("#995233"))
            elif i in crypto:
                item.setBackground(QColor("#429933"))
            else:
                item.setBackground(QColor("#365e99"))

    @err_catcher(name=__name__)
    def sm_render_addRenderPass(self, origin, passName, steps, layername):
        self.enableViewLayerAOV(passName, layername)

    @err_catcher(name=__name__)
    def sm_render_openPasses(self, origin, item=None):
        #Called when passes list widget lw_passes is double clicked.
        pass

    @err_catcher(name=__name__)
    def getNodeAOVs(self):
        if bpy.context.scene.node_tree is None or not bpy.context.scene.use_nodes:
            return

        outNodes = [
            x for x in bpy.context.scene.node_tree.nodes if x.type == "OUTPUT_FILE"
        ]
        rlayerNodes = [
            x for x in bpy.context.scene.node_tree.nodes if x.type == "R_LAYERS"
        ]

        passNames = []

        for m in outNodes:
            connections = []
            for i in m.inputs:
                if len(list(i.links)) > 0:
                    connections.append(i.links[0])

            for i in connections:
                passName = i.from_socket.name

                if passName == "Image":
                    passName = "beauty"

                if i.from_node.type == "R_LAYERS":
                    if len(rlayerNodes) > 1:
                        passName = "%s_%s" % (i.from_node.layer, passName)

                else:
                    if hasattr(i.from_node, "label") and i.from_node.label != "":
                        passName = i.from_node.label

                passNames.append(passName)

        return passNames

    @err_catcher(name=__name__)
    def getViewLayerAOVs(self, layername)->list:
        scene = bpy.context.scene
        availableAOVs = self.getAvailableAOVs(layername)
        # curlayer = bpy.context.window_manager.windows[0].view_layer
        curlayer = scene.view_layers[layername]
        aovNames = []
        for aa in availableAOVs:
            val = None
            try:
                val = operator.attrgetter(aa["parm"])(curlayer)
            except AttributeError:
                logging.debug("Couldn't access aov %s" % aa["parm"])

            if val:
                aovNames.append(aa["name"])

        return aovNames

    @err_catcher(name=__name__)
    def getAvailableAOVs(self, layername)->list:
        scene = bpy.context.scene
        # curlayer = bpy.context.window_manager.windows[0].view_layer
        curlayer = scene.view_layers[layername]
        aovParms = [x for x in dir(curlayer) if x.startswith("use_pass_")]
        # AOVs inside the cycles list
        if self.isUsingCycles():
            aovParms += [
                "cycles." + x for x in dir(curlayer.cycles) if x.startswith("use_pass_")
            ]
        elif self.isUsingEevee():
            aovParms += [
                "eevee." + x for x in dir(curlayer.eevee) if x.startswith("use_pass_")
            ]
        aovs = [
            {"name": "Denoising Data", "parm": "cycles.denoising_store_passes"},
            {"name": "Debug Samples", "parm": "cycles.pass_debug_sample_count"},
        ]
        nameOverrides = {
            "Emit": "Emission",
        }
        for aov in aovParms:
            name = aov.replace("use_pass_", "").replace("cycles.", "").replace("eevee.","")
            name = [x[0].upper() + x[1:] for x in name.split("_")]
            name = " ".join(name)
            name = nameOverrides[name] if name in nameOverrides else name
            if(name.lower() in self.AOVDict.keys()):
                aovs.append({"name": name, "parm": aov})

        aovs = sorted(aovs, key=lambda x: x["name"])

        return aovs

    @err_catcher(name=__name__)
    def useNodeAOVs(self)->bool:
        return bool(self.getNodeAOVs())

    
    @err_catcher(name=__name__)
    def getPatternedLayerNodes(self, pattern):
        nodes = []
        for node in bpy.context.scene.node_tree.nodes:
            if node.type == 'R_LAYERS':
                if node.name == pattern + node.layer:
                    nodes.append(node)
        return nodes

    @err_catcher(name=__name__)
    def sortNodesByYposition(self, nodes:list)->list:
        return sorted(nodes, key=lambda node: node.location.y, reverse=True)
    
    @err_catcher(name=__name__)
    def getRLDimensions(self, renderlayernode)->float:
        outs = [o for o in renderlayernode.outputs if o.enabled == True]
        basedimension:float = 79
        buffer:float = 100
        outputdimension:float = 22

        return (basedimension + buffer + (len(outs)*outputdimension))
         

    @err_catcher(name=__name__)
    def repositionRenderLayerNodes(self)->None:
        nodes:list = self.getPatternedLayerNodes('Prism_RL_')
        if len(nodes) > 0:
            sorted_nodes:list = self.sortNodesByYposition(nodes)
            y_offset:float = 0
            current_y:float = sorted_nodes[0].location.y
            current_x:float = sorted_nodes[0].location.x
            for node in sorted_nodes:
                layername:str = node.layer
                node.location = mathutils.Vector((current_x,current_y))
                self.repositionLayerOutNodes(layername=layername, in_node=node)
                out_node_dimensions:float = 0.0
                layernodesdict:dict = self.getLayerOutNodes(layername)
                if layernodesdict['main']:
                    out_node_dimensions += (75.27 + (len(layernodesdict['main'].inputs) * 22))
                if layernodesdict['tech']:
                    out_node_dimensions += (75.27 + (len(layernodesdict['tech'].inputs) * 22))
                if layernodesdict['crypto']:
                    out_node_dimensions += (75.27 + (len(layernodesdict['crypto'].inputs) * 22))
                
                max_dimension = out_node_dimensions
                if self.getRLDimensions(node) > max_dimension:
                    max_dimension = self.getRLDimensions(node)
                
                current_y -= max_dimension + y_offset


    @err_catcher(name=__name__)
    def repositionLayerOutNodes(self, layername:str, in_node=None)->None:
        if not in_node:
            in_node = self.getRLNode(layername)
        layernodesdict:dict = self.getLayerOutNodes(layername)
        out_node = layernodesdict['main']
        ##Cambiar la pos de Tech, Main y Crypto en Y dependiendo del numero de inputs que tenga
        ## las dimensiones de un Outnode son 69.0 (con un pequeño buffer es 75.27) + 22*el número de inputs 
        x_offset = (in_node.width + 240)
        y_offset = 100
        
        out_node.location = in_node.location + mathutils.Vector((x_offset,0.0))
        if layernodesdict['tech']:
            out_node_tech = layernodesdict['tech']
            y_dimension = 75.27 + (len(out_node_tech.inputs)*22)# + y_offset
            out_node_tech.location = in_node.location + mathutils.Vector((x_offset,0.0))
            #Ponemos el OutNode en relacion al TechNode
            out_node.location = out_node_tech.location + mathutils.Vector((0,-y_dimension))
        if layernodesdict['crypto']:
            out_node_Crypto = layernodesdict['crypto']
            y_dimension = 75.27 + (len(out_node_Crypto.inputs)*22)
            out_node_y_dimension = 75.27 + (len(out_node.inputs)*22)
            out_node_Crypto.location = out_node.location + mathutils.Vector((0,-out_node_y_dimension))

    @err_catcher(name=__name__)
    def removeEmptyOutNodes(self, layername:str)->None:
        layernodesdict:dict = self.getLayerOutNodes(layername)
        for node in list(layernodesdict.values()):
            if node:
                if len(node.inputs) < 1:
                    bpy.context.scene.node_tree.nodes.remove(node)

    @err_catcher(name=__name__)
    def removeAOVSlot(self, layernodes:dict, nodetype:str, slotname:str)->None:
        if layernodes[nodetype]:
            inputs = layernodes[nodetype].inputs
            if slotname in inputs:
                inputs.remove(inputs[slotname])

    @err_catcher(name=__name__)
    def removeAOV(self, aovName:str, renderlayerName:str)->None:
        if True:#self.useNodeAOVs():
            nodeAovName:str = self.AOVDict[aovName.lower()]
            layernodesdict:dict = self.getLayerOutNodes(renderlayerName)            
            slotname:str = self.getSlotname(renderlayerName, nodeAovName)

            if self.compareTechPass(nodeAovName):
                self.removeAOVSlot(layernodesdict, 'tech', slotname)
            elif self.isCryptoPass(nodeAovName):
                # for Cryptos the slot has to be named like the pass.
                cryptoindexes = ['00','01','02']
                for cri in cryptoindexes:
                    slotname = nodeAovName+cri
                    self.removeAOVSlot(layernodesdict, 'crypto', slotname)
            else:
                if nodeAovName == "Denoising":
                    denoisepasses = ['Normal','Albedo','Depth']
                    for aov in denoisepasses:
                        slotname = self.getSlotname(renderlayerName, nodeAovName+" "+aov)
                        self.removeAOVSlot(layernodesdict, 'main', slotname)
                else:
                    self.removeAOVSlot(layernodesdict, 'main', slotname)
        
        self.enableViewLayerAOV(aovName, renderlayerName, enable=False)


    @err_catcher(name=__name__)
    def enableViewLayerAOV(self, name, layername, enable=True):
        aa = self.getAvailableAOVs(layername)
        curAOV = [x for x in aa if x["name"] == name]
        if not curAOV:
            return

        curAOV = curAOV[0]
        
        scene = bpy.context.scene
        curlayer = scene.view_layers[layername]
        
        attrs = curAOV["parm"].split(".")
        obj = curlayer
        #Choose last index from splited string. example cycles.use_pass_volume_indirect we get use_pass_volume_indirect only.
        for a in attrs[:-1]:
            # here the obj becomes layer.cycles or layer.eevee where is applicable instead of just layer
            obj = getattr(obj, a)

        setattr(obj, attrs[-1], enable)

    @err_catcher(name=__name__)
    def setViewLayerPropertyState(self, parameter, layername, enable)->None:
        scene = bpy.context.scene
        curlayer = scene.view_layers[layername]
        attrs = parameter.split(".")
        obj = curlayer
        for a in attrs[:-1]:
            #obj = getattr(obj, 'cycles')
            obj = getattr(obj, a)
        setattr(obj, attrs[-1], enable)

    @err_catcher(name=__name__)
    def getViewLayerPropertyState(self, parameter, layername)->bool:
        scene = bpy.context.scene
        curlayer = scene.view_layers[layername]
        attrs = parameter.split(".")
        obj = curlayer
        for a in attrs[:-1]:
            #obj = getattr(obj, 'cycles')
            obj = getattr(obj, a)
        ischecked = getattr(obj, attrs[-1])
        return ischecked


    ######################################
    #                                    #
    ####### MH ORIGINAL FUNCTIONS ########
    #                                    #
    ######################################

    ######___FUNCIONES_SETPASS___######
    @err_catcher(name=__name__)
    def nodeNameExists(self, node_name):
        node_tree = bpy.context.scene.node_tree
        # Iterate through all nodes in the node tree
        for node in node_tree.nodes:
            if node.name == node_name:
                return True
        return False

    @err_catcher(name=__name__)
    def setUpOutNode(self, out_node, basepath, name, depth, node_color, fformat):
        out_node.width *= 2
        out_node.base_path = basepath
        out_node.format.file_format = fformat
        out_node.format.color_depth = str(depth)
        out_node.format.color_mode = 'RGBA'
        out_node.file_slots.remove(out_node.inputs[0])
        out_node.name = name
        out_node.label = name.replace("_", " ")
        out_node.use_custom_color = True
        out_node.color = node_color
        return out_node

    @err_catcher(name=__name__)
    def getSlotname(self, layername, aovname):
        if aovname == "Image":
            aovname = "beauty"
        return layername + "_" + aovname + "/" + layername + "_" + aovname + "_####.exr"

    @err_catcher(name=__name__)
    def connectNodes(self, nodetree, layername, renderpass, out_node)->None:
        if renderpass.is_linked:
            return
        aovname = renderpass.name
        slotname = self.getSlotname(layername, aovname)
        # for Cryptos the slot has to be named like the pass.
        if "CryptoMatte" in out_node.label:
            slotname = aovname
        # if already slot exists, connect to existing.
        inputs_by_name = [p.name for p in out_node.inputs]
        if slotname in inputs_by_name:
            if not out_node.inputs[slotname].is_linked:
                slot = out_node.inputs[slotname]
        else:
            slot = out_node.file_slots.new(slotname)
        links = nodetree.links
        link = links.new(renderpass,slot)

    @err_catcher(name=__name__)
    def checkTechPasses(self, currentpasses)->bool:
        for currentpass in currentpasses:
            if self.compareTechPass(currentpass.name):
                return True
        return False
    
    @err_catcher(name=__name__)
    def compareTechPass(self, currentpassname:str)->bool:
        techPasses = ['Depth','Normal','UV','Vector','Mist','Position']
        if currentpassname in techPasses:
            return True
        return False

    @err_catcher(name=__name__)
    def hasCryptoObj(self, passesbyname:list)->bool:
        return 'CryptoObject00' in passesbyname
    
    @err_catcher(name=__name__)
    def hasCryptoMat(self, passesbyname:list)->bool:
        return 'CryptoMaterial00' in passesbyname
    
    @err_catcher(name=__name__)
    def hasCryptoAsset(self, passesbyname:list)->bool:
        return 'CryptoAsset00' in passesbyname

    @err_catcher(name=__name__)
    def isCryptoPass(self, currentpassname:str)->bool:
        return 'Crypto' in currentpassname

    ## Output node making functions ##
    @err_catcher(name=__name__)
    def get_output_node(self, node_path:str, node_name:str, img_bitdepth:int, color, fformat:str):
        nodetree = bpy.context.scene.node_tree
        node_name = 'Prism_OUT_' + node_name
        if self.nodeNameExists(node_name):
            out_node = nodetree.nodes[node_name]
        else:
            out_node = nodetree.nodes.new(type='CompositorNodeOutputFile')
            out_node = self.setUpOutNode(out_node, node_path, node_name, img_bitdepth, color, fformat)
        return out_node

    @err_catcher(name=__name__)
    def get_MainOutode(self, allpath, layername):
        out_node = self.get_output_node(allpath, layername+'_MainPasses', 16, (0.21, 0.37, 0.6), 'OPEN_EXR')
        return out_node
    
    @err_catcher(name=__name__)
    def get_TecOuthNode(self, allpath, layername):
        out_node = self.get_output_node(allpath,layername+'_TechPasses', 32, (0.6, 0.32, 0.2), 'OPEN_EXR')
        return out_node
    
    @err_catcher(name=__name__)
    def get_CryptoOutNode(self, allpath, layername):
        out_node = self.get_output_node(allpath + "/" + layername + "_CryptoMatte",layername+'_CryptoMatte', 32, (0.26, 0.6, 0.2), 'OPEN_EXR_MULTILAYER')
        return out_node

    @err_catcher(name=__name__)
    def make_CryptoConnections(self, nodetree, layername, layerpass, out_node_Crypto):
        cryptoindex = ['00','01','02']
        for i in cryptoindex:
            if i in layerpass.name:
                self.connectNodes(nodetree, layername, layerpass, out_node_Crypto)

    @err_catcher(name=__name__)
    def lastRLlocation(self):
        lowest_y = float('inf')
        lowest_y_node = None
        nodetree = bpy.context.scene.node_tree
        rendernodes = [n for n in nodetree.nodes if n.type == 'R_LAYERS']
        if len(rendernodes) < 1:
            return None, mathutils.Vector((0,0))
        
        for n in rendernodes:
            if n.location.y < lowest_y:
                lowest_y = n.location.y
                lowest_y_node = n
        
        return lowest_y_node, lowest_y_node.location + mathutils.Vector((0, -lowest_y_node.dimensions[1]))

    @err_catcher(name=__name__)
    def getRLNode(self, layername, cancreate=True):
        nodename = 'Prism_RL_' + layername
        nodetree = bpy.context.scene.node_tree
        rendernodes = [n for n in nodetree.nodes if n.type == 'R_LAYERS']
        rendernode = None
        for n in rendernodes:
            if n.layer == layername:
                if n.name == nodename:
                    rendernode = n

        if not rendernode and cancreate:
            nodes:list = self.getPatternedLayerNodes('Prism_RL_')
            sorted_nodes:list = self.sortNodesByYposition(nodes)

            if len(sorted_nodes) > 0:
                lowernode =  sorted_nodes[-1]
                lowerloc = lowernode.location
                y_offset = self.getRLDimensions(lowernode)
            else:
                lowernode = None
                lowerloc = mathutils.Vector((0,0))
                y_offset = 0
            layer_node = nodetree.nodes.new(type='CompositorNodeRLayers')
            layer_node.name = nodename
            layer_node.label = "Prism RL " + layername
            layer_node.layer = layername
            layer_node.location = lowerloc + mathutils.Vector((0, -y_offset))
            rendernode = layer_node

        return rendernode

    # mute nodes if layer is disabled
    @err_catcher(name=__name__)
    def toggleLayerNodes(self, layername:str, toggle:bool)->None:
        nodename = 'Prism_RL_' + layername
        nodetree = bpy.context.scene.node_tree
        rendernodes = [n for n in nodetree.nodes if n.type == 'R_LAYERS']
        rendernode = None
        for n in rendernodes:
            if n.layer == layername:
                if n.name == nodename:
                    rendernode = n
        if rendernode:
            layernodesdict:dict = self.getLayerOutNodes(layername)
            for out_node in list(layernodesdict.values()):
                if out_node:
                    out_node.mute = toggle
            rendernode.mute = toggle

        if layername in self.getRenderLayers():
            bpy.context.scene.view_layers[layername].use = not toggle

    
    ##################################

    ##FUNCION PRINCIPAL
    # !CallFromMHRendLayer
    @err_catcher(name=__name__)
    def createOutputFromRL(self, layername, basepath = ""):
        if not bpy.context.scene.use_nodes:
            bpy.context.scene.use_nodes = True
            nodetree = bpy.context.scene.node_tree
            # Eliminar el nodo de render layers por default
            defaultNode = nodetree.nodes[1]
            if defaultNode:
                if defaultNode.type == 'R_LAYERS':
                    if defaultNode.name == 'Render Layers':
                        nodetree.nodes.remove(defaultNode)
        
        nodetree = bpy.context.scene.node_tree
        n = self.getRLNode(layername)
        if n.type == 'R_LAYERS':
            in_node = n
            allpath = basepath
            out_node = self.get_MainOutode(allpath, layername)
            enabled_passes = [p for p in in_node.outputs if p.enabled]
            passes_by_name = [p.name for p in enabled_passes]
            techEnabled = self.checkTechPasses(enabled_passes)
            cryptoOEnabled = self.hasCryptoObj(passes_by_name)
            cryptoMEnabled = self.hasCryptoMat(passes_by_name)
            cryptoAEnabled = self.hasCryptoAsset(passes_by_name)
            ##Checar si hay nodos que cuenten como TechPasses
            if techEnabled:
                out_node_tech = self.get_TecOuthNode(allpath, layername)
            #Checar los Cryptomattes
            if cryptoOEnabled or cryptoMEnabled or cryptoAEnabled:
                out_node_Crypto = self.get_CryptoOutNode(allpath, layername)    

            ##Hacer las conexiones
            for o in enabled_passes:
                if self.compareTechPass(o.name):
                    self.connectNodes(nodetree, layername, o, out_node_tech)
                elif self.isCryptoPass(o.name):
                    self.make_CryptoConnections(nodetree, layername, o, out_node_Crypto)
                else:
                    self.connectNodes(nodetree, layername, o, out_node)
                
            # self.repositionLayerOutNodes(layername)
            self.repositionRenderLayerNodes()

    ###########################

    ######___FUNCIONES_PATH___######
    # !CallFromMHRendLayer
    @err_catcher(name=__name__)
    def setOutputsPaths(self, layername, basepath):
        nodetree = bpy.context.scene.node_tree
        layernodesdict:dict = self.getLayerOutNodes(layername)
        for key, value in layernodesdict.items():
            node = value
            if node and node.type == 'OUTPUT_FILE':
                # Remove the AOV beauty from the base path
                allpath = os.path.dirname(os.path.normpath(basepath + "\\"))
                if key == 'crypto':
                    allpath = os.path.normpath(os.path.join(allpath, layername + "_Cryptomatte", layername + "_CryptoMatte_####.exr"))

                node.base_path = allpath


    ###########################
    @err_catcher(name=__name__)
    def removeUnconnectedInputs(self, node):
        for i in node.inputs:
            if len(i.links) == 0:
                node.inputs.remove(i)
  
    @err_catcher(name=__name__)
    def getLayerOutNodes(self, layername) -> dict:
        nodetree = bpy.context.scene.node_tree
        outnodes = {
            'main':None,
            'tech':None,
            'crypto':None,
            }
        nodename = 'Prism_OUT_' + layername + '_MainPasses'
        if self.nodeNameExists(nodename):
            outnodes['main'] = nodetree.nodes[nodename]
        nodename = 'Prism_OUT_' + layername + '_TechPasses'
        if self.nodeNameExists(nodename):
            outnodes['tech'] = nodetree.nodes[nodename]
        nodename = 'Prism_OUT_' + layername + '_CryptoMatte'
        if self.nodeNameExists(nodename):
            outnodes['crypto'] = nodetree.nodes[nodename]

        return outnodes


    ######################################
    #                                    #
    #######   MHRenderFunctions   ########
    #                                    #
    ######################################
    @err_catcher(name=__name__)
    def sm_render_preSubmit(self, origin, rSettings):
        if origin.chb_resOverride.isChecked():
            rSettings["width"] = bpy.context.scene.render.resolution_x
            rSettings["height"] = bpy.context.scene.render.resolution_y
            bpy.context.scene.render.resolution_x = origin.sp_resWidth.value()
            bpy.context.scene.render.resolution_y = origin.sp_resHeight.value()

        imgFormat = origin.cb_format.currentText()        
        if imgFormat == ".jpg":
            fileFormat = "JPEG"

        rSettings["prev_start"] = bpy.context.scene.frame_start
        rSettings["prev_end"] = bpy.context.scene.frame_end
        rSettings["fileformat"] = bpy.context.scene.render.image_settings.file_format
        rSettings["overwrite"] = bpy.context.scene.render.use_overwrite
        rSettings["fileextension"] = bpy.context.scene.render.use_file_extension
        rSettings["resolutionpercent"] = bpy.context.scene.render.resolution_percentage
        rSettings["origOutputName"] = rSettings["outputName"]
        bpy.context.scene["PrismIsRendering"] = True
        bpy.context.scene.render.filepath = rSettings["outputName"]
        bpy.context.scene.render.image_settings.file_format = fileFormat
        bpy.context.scene.render.use_overwrite = True
        bpy.context.scene.render.use_file_extension = False
        bpy.context.scene.render.resolution_percentage = 100
        bpy.context.scene.camera = bpy.context.scene.objects[origin.curCam]

        if not os.path.exists(os.path.dirname(rSettings["outputName"])):
            os.makedirs(os.path.dirname(rSettings["outputName"]))


    ######################################
    #                                    #
    #######       CALLBACKS       ########
    #                                    #
    ######################################

    @err_catcher(name=__name__)
    def onStateDeleted(self, stateManager, state, *args, **kwargs)->None:
        if state.className == "MHrendLayer":
            layername = state.cb_renderLayer.currentText()
            try:
                rlnode = bpy.context.scene.node_tree.nodes['Prism_RL_' + layername]
            except:
                rlnode = None
            if rlnode:
                message = f"Delete nodes asociated with this Layer?"
                result = self.core.popupQuestion(
                    message,
                    title="Create new Layer?",
                )
                if result == "Yes":                    
                    layernodesdict:dict = self.getLayerOutNodes(layername)
                    for l in list(layernodesdict.values()):
                        if l:
                            bpy.context.scene.node_tree.nodes.remove(l)
                    bpy.context.scene.node_tree.nodes.remove(rlnode)
                    self.repositionRenderLayerNodes()
            
