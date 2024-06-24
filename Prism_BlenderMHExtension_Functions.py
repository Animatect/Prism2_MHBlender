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

    @err_catcher(name=__name__)
    def startup(self):
        print("plugin está en startup.")

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

        passNames = self.getNodeAOVs()
        logger.debug("node aovs: %s" % passNames)
        origin.b_addPasses.setVisible(not passNames)
        self.blenderplugin.canDeleteRenderPasses = bool(not passNames)
        if not passNames:
            passNames = self.getViewLayerAOVs(origin.cb_renderLayer.currentText())
            logger.debug("viewlayer aovs: %s" % passNames)

        if passNames:
            origin.lw_passes.addItems(passNames)

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
    def getViewLayerAOVs(self, layername):
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
    def getAvailableAOVs(self, layername):
        scene = bpy.context.scene
        # curlayer = bpy.context.window_manager.windows[0].view_layer
        curlayer = scene.view_layers[layername]
        aovParms = [x for x in dir(curlayer) if x.startswith("use_pass_")]
        aovParms += [
            "cycles." + x for x in dir(curlayer.cycles) if x.startswith("use_pass_")
        ]
        aovs = [
            {"name": "Denoising Data", "parm": "cycles.denoising_store_passes"},
            {"name": "Render Time", "parm": "cycles.pass_debug_render_time"},
        ]
        nameOverrides = {
            "Emit": "Emission",
        }
        for aov in aovParms:
            name = aov.replace("use_pass_", "").replace("cycles.", "")
            name = [x[0].upper() + x[1:] for x in name.split("_")]
            name = " ".join(name)
            name = nameOverrides[name] if name in nameOverrides else name
            aovs.append({"name": name, "parm": aov})

        aovs = sorted(aovs, key=lambda x: x["name"])

        return aovs

    @err_catcher(name=__name__)
    def useNodeAOVs(self):
        return bool(self.getNodeAOVs())

    @err_catcher(name=__name__)
    def removeAOV(self, aovName, renderlayerName):
        if self.useNodeAOVs():
            rlayerNodes = [
                x for x in bpy.context.scene.node_tree.nodes if x.type == "R_LAYERS"
            ]

            for m in rlayerNodes:
                connections = []
                for i in m.outputs:
                    if len(list(i.links)) > 0:
                        connections.append(i.links[0])
                        break

                for i in connections:
                    if i.to_node.type == "OUTPUT_FILE":
                        for idx, k in enumerate(i.to_node.file_slots):
                            links = i.to_node.inputs[idx].links
                            if len(links) > 0:
                                if links[0].from_socket.node != m:
                                    continue

                                passName = links[0].from_socket.name
                                layerName = links[0].from_socket.node.layer

                                if passName == "Image":
                                    passName = "beauty"

                                if (
                                    passName == aovName.split("_", 1)[1]
                                    and layerName == aovName.split("_", 1)[0]
                                ):
                                    i.to_node.inputs.remove(i.to_node.inputs[idx])
                                    return
        else:
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
        for a in attrs[:-1]:
            obj = getattr(obj, a)

        setattr(obj, attrs[-1], enable)

###################################################################

    
