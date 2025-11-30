# Blender Extension for internal use at Magic Hammer Studios

import os
import sys
import traceback
import logging

from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *


from PrismUtils.Decorators import err_catcher

from Prism_MHExtension_Integration import Prism_MHExtension_Integration

logger = logging.getLogger(__name__)

dirnm = os.path.dirname(__file__)
extra_paths = [os.path.abspath(os.path.join(dirnm, 'StateManagerNodes')), os.path.abspath(os.path.join(dirnm, 'StateManagerNodes', 'StateUserInterfaces'))]
for extra_path in extra_paths:
    if extra_path not in sys.path:
        sys.path.append(extra_path)


class Prism_MHExtension_Functions(object):
    def __init__(self, core, plugin):
        self.core = core
        self.plugin = plugin
        self.blendFunctions = None
        self.fusFunctions = None
        self.monkeypatchedsm = None
        self.customstates = ["bld_MHRender", "bld_MHrendLayer"]
        self.isMHrendClass = False
        
        #   Callbacks
        logger.debug("Loading callbacks")
        self.core.registerCallback("userSettings_loadUI", self.onUserSettings_loadUI, plugin=self)
        self.core.registerCallback("onStateManagerOpen", self.onStateManagerOpen, plugin=self)
        self.core.registerCallback("pluginLoaded", self.onPluginLoaded, plugin=self)
        # Register callback for ProductBrowser
        self.core.registerCallback("onProductBrowserOpen", self.onProductBrowserOpen, plugin=self.plugin)

        self.core.registerCallback("userSettings_saveSettings",self.userSettings_saveSettings,plugin=self.plugin,)
        self.core.registerCallback("userSettings_loadSettings",self.userSettings_loadSettings,plugin=self.plugin,)

    # if returns true, the plugin will be loaded by Prism
    @err_catcher(name=__name__)
    def isActive(self):
        return True
    
    @err_catcher(name=__name__)
    def onUserSettings_loadUI(self, origin):
        self.userSettings_loadUI(origin)
    
    @err_catcher(name=__name__)
    def onStateManagerOpen(self, origin):
        for customstate in self.customstates:
            if self.core.appPlugin.appShortName.lower() == "bld":
                self.monkeypatchedsm = origin
                #
                self.core.plugins.monkeyPatch(origin.rclTree, self.rclTree, self, force=True)
                self.core.plugins.monkeyPatch(self.core.appPlugin.sm_export_exportShotcam, self.sm_export_exportShotcam, self, force=True)
                self.core.plugins.monkeyPatch(self.core.appPlugin.sm_playblast_createPlayblast, self.sm_playblast_createPlayblast, self, force=True)
                #
                self.stateTypeCreator(customstate, origin)
            
            if self.core.appPlugin.appShortName.lower() == "fus":
                if self.fusFunctions:
                    self.fusFunctions.sm_extendFusionPlugin(origin)
                    self.core.plugins.monkeyPatch(self.core.appPlugin.shotCam, self.fusFunctions.shotCam, self, force=True)
                
    @err_catcher(name=__name__)
    def onPluginLoaded(self, plugin):
        if not self.blendFunctions:
            if self.core.appPlugin.appShortName.lower() == "bld":
                import Prism_BlenderMHExtension_Functions
                self.blendFunctions = Prism_BlenderMHExtension_Functions.Prism_BlenderMHExtension_Functions(self.core, self.core.appPlugin)
                # self.applyPatch(plugin)
                self.core.plugins.monkeyPatch(self.core.products.getVersionStackContextFromPath, self.getVersionStackContextFromPath, self, force=True)
                # Add custom export handler for .mhUsd files
                self.core.appPlugin.exportHandlers[".mhUsd"] = {"exportFunction": self.core.appPlugin.exportUsd}
                # Add .mhUsd to the output formats list if not already present
                if ".mhUsd" not in self.core.appPlugin.outputFormats:
                    self.core.appPlugin.outputFormats.append(".mhUsd")
                    logger.debug("Added .mhUsd to outputFormats")
        if not self.fusFunctions:
            if self.core.appPlugin.appShortName.lower() == "fus":
                import Prism_FusionMHExtension_Functions
                self.fusFunctions = Prism_FusionMHExtension_Functions.Prism_FusionMHExtension_Functions(self.core, self.core.appPlugin)

    		
    @err_catcher(name=__name__)
    def onProductBrowserOpen(self, productBrowser):
        """
        Callback when ProductBrowser opens. Monkey patches the updateIdentifiers method
        to automatically group usdlayer_* products under ASSET products.
        ASSET will appear as both a selectable product AND a group containing usdlayer items.
        """
        logger.debug("ProductBrowser opened - applying ASSET grouping logic")

        # Store the original updateIdentifiers method
        original_updateIdentifiers = productBrowser.updateIdentifiers
        # Store the original createGroupItems method
        original_createGroupItems = productBrowser.createGroupItems

        # Wrapper for createGroupItems to handle ASSET as both item and group
        def custom_createGroupItems(identifiers):
            # Call original method to get groups and group items
            groups, groupItems = original_createGroupItems(identifiers)

            # Find if ASSET exists and if there are usdlayer_* products grouped under it
            if "ASSET" in groupItems and "ASSET" in identifiers:
                # Replace the group-only item with a hybrid item
                assetGroupItem = groupItems["ASSET"]
                assetData = identifiers["ASSET"]

                # Clear the "isGroup" flag and add the actual product data
                assetGroupItem.setData(0, Qt.UserRole, assetData)

                # Update the display text to show it's a product (remove folder-only appearance)
                assetGroupItem.setText(0, "ASSET")

                # Set custom icon for ASSET
                iconPath = r"C:\Users\ecovo\Documents\GitHub\Prism2_MHBlender\MHExtension\Integrations\Icons\addasset.svg"
                if os.path.exists(iconPath):
                    icon = self.core.media.getColoredIcon(iconPath)
                    assetGroupItem.setIcon(0, icon)
                    logger.debug(f"Set custom icon for ASSET from: {iconPath}")
                else:
                    logger.warning(f"ASSET icon not found at: {iconPath}")

                logger.debug("Modified ASSET to be both group and selectable product")

            return groups, groupItems

        # Create wrapper function that adds our custom grouping logic
        def custom_updateIdentifiers(item=None, restoreSelection=False):
            # Get all identifiers before modification
            identifiers = productBrowser.getIdentifiers()

            # Auto-group usdlayer_* products under ASSET
            for identifierName in list(identifiers.keys()):
                # Check if this is a usdlayer_* product
                if identifierName.startswith("usdlayer_"):
                    # Check if ASSET product exists in the same entity
                    if "ASSET" in identifiers:
                        # Set the group for this usdlayer product
                        self.core.products.setProductsGroup(
                            [identifiers[identifierName]],
                            group="ASSET"
                        )
                        logger.debug(f"Auto-grouped {identifierName} under ASSET")

            # Call the original updateIdentifiers method
            # Handle both function signatures (with or without 'item' parameter)
            import inspect
            try:
                sig = inspect.signature(original_updateIdentifiers)
                params = list(sig.parameters.keys())

                # Call with appropriate parameters based on signature
                if 'item' in params:
                    original_updateIdentifiers(item=item, restoreSelection=restoreSelection)
                else:
                    original_updateIdentifiers(restoreSelection=restoreSelection)
            except:
                # Fallback: try calling with just restoreSelection
                try:
                    original_updateIdentifiers(restoreSelection=restoreSelection)
                except:
                    # Last resort: call with no arguments
                    original_updateIdentifiers()

        # Replace both methods with our custom versions
        productBrowser.createGroupItems = custom_createGroupItems
        productBrowser.updateIdentifiers = custom_updateIdentifiers

    @err_catcher(name=__name__)
    def is_object_excluded_from_view_layer(self, obj):
        import bpy
        view_layer = bpy.context.view_layer

        for collection in obj.users_collection:
            # Check if the collection is excluded from the view layer
            layer_collection = view_layer.layer_collection
            collection_in_layer = layer_collection.children.get(collection.name)
            if collection_in_layer and collection_in_layer.exclude:
                return True

        return False

    @err_catcher(name=__name__)
    def sm_export_exportShotcam(self, origin, startFrame, endFrame, outputName):
        import bpy
        if origin.curCam in bpy.data.objects:
            cam = bpy.data.objects[origin.curCam]
            if self.is_object_excluded_from_view_layer(cam) or cam.hide_get():
                self.core.popup("Object not visible in viewport at the moment")
            else:
                self.core.plugins.callUnpatchedFunction(self.core.appPlugin.sm_export_exportShotcam, origin, startFrame, endFrame, outputName)
                self.blendFunctions.sm_export_exportBlenderShotcam(origin, startFrame, endFrame, outputName, self.core.appPlugin)
        # print("is monkeypatched: ", "\norigin: ", origin, "\nstartFrame: ", startFrame, ", endFrame: ", endFrame, "\noutputName: ", outputName, "\n#######\n")

    @err_catcher(name=__name__)
    def stateTypeCreator(self, stateName, stateManager):
        stateNameBase = stateName
        stateNameBase = stateNameBase.replace(stateName.split("_", 1)[0] + "_", "" )
        if stateNameBase in stateManager.stateTypes and stateName not in stateManager.forceStates:
            return
        stateUi = stateName + "_ui"
        if eval(os.getenv("PRISM_DEBUG", "False")):
            try:
                del sys.modules[stateName]
            except:
                pass
            try:
                del sys.modules[stateName + "_ui"]
            except:
                pass

        try:
            exec(
                """
import %s
import %s
class %s(QWidget, %s.%s, %s.%sClass):
    def __init__(self):
        QWidget.__init__(self)
        self.setupUi(self)"""
                    % (
                        stateName,
                        stateUi,
                        stateNameBase + "Class",
                        stateName + "_ui",
                        "Ui_wg_" + stateNameBase,
                        stateName,
                        stateNameBase,
                    )
            )
            validState = True
        except:
            logger.warning(traceback.format_exc())
            validState = False

        if validState:
            classDef = eval(stateNameBase + "Class")
            stateManager.loadState(classDef)


    ################################################
    #                                              #
    #        	 MONKEYPATCHED FUNCTIONS           #
    #                                              #
    ################################################
    
    #Right click menu from nodes on state manager to get previous versions.
    @err_catcher(name=__name__)
    def rclTree(self, pos, activeList):
        sm = self.monkeypatchedsm
        if sm:
            renderclasses = ["MHrendLayer", "MHRender"]
            # we chack if the rclick is over a state
            idx = sm.activeList.indexAt(pos)
            parentState = sm.activeList.itemFromIndex(idx)
            if parentState:
                # if the action is over one of the MH states we turn the variable on to inform the
                # other monkeypatched functions that the modified version should be used.
                self.isMHrendClass = parentState.ui.className in renderclasses
                if self.isMHrendClass:
                    rcmenu = QMenu(sm)
                    sm.rClickedItem = parentState

                    actExecute = QAction("Execute", sm)
                    # successPopup is being handled in the export state for these states.
                    actExecute.triggered.connect(lambda: sm.publish(executeState=True,successPopup=False))

                    menuExecuteV = QMenu("Execute as previous version", sm)

                    actSort = None
                    selItems = sm.getSelectedStates()
                    if len(selItems) > 1:
                        parents = []
                        for item in selItems:
                            if item.parent() not in parents:
                                parents.append(item.parent())

                        if len(parents) == 1:
                            actSort = QAction("Sort", sm)
                            actSort.triggered.connect(lambda: sm.sortStates(selItems))

                    actCopy = QAction("Copy", sm)
                    actCopy.triggered.connect(sm.copyState)

                    actPaste = QAction("Paste", sm)
                    actPaste.triggered.connect(sm.pasteStates)

                    actRename = QAction("Rename", sm)
                    actRename.triggered.connect(sm.renameState)

                    actDel = QAction("Delete", sm)
                    actDel.triggered.connect(sm.deleteState)

                    if parentState is None:
                        actCopy.setEnabled(False)
                        actRename.setEnabled(False)
                        actDel.setEnabled(False)
                        actExecute.setEnabled(False)
                        menuExecuteV.setEnabled(False)
                    elif hasattr(parentState.ui, "l_pathLast"):
                        outPath = parentState.ui.getOutputName()
                        if not outPath or not outPath[0]:
                            menuExecuteV.setEnabled(False)
                        else:
                            outPath = outPath[0]
                            if "rend" in parentState.ui.className.lower():
                                existingVersions = self.core.mediaProducts.getVersionsFromSameVersionStack(
                                    outPath, mediaType="3drenders"
                                )
                            elif "playblast" in parentState.ui.className.lower():
                                existingVersions = sm.core.mediaProducts.getVersionsFromSameVersionStack(
                                    outPath, mediaType="playblasts"
                                )
                            else:
                                existingVersions = sm.core.products.getVersionsFromSameVersionStack(
                                    outPath, mediaType="3drenders"
                                )
                            
                            if parentState.ui.className == "MHRender":
                                actV = None
                                for version in sorted(
                                    existingVersions, key=lambda x: x["version"], reverse=True
                                ):
                                    name = "last version"
                                    actV = QAction(name, sm)
                                    actV.triggered.connect(
                                        lambda y=None, v=version["version"]: sm.publish(
                                            executeState=True, useVersion=v
                                        )
                                    )
                                if actV:
                                    menuExecuteV.addAction(actV)
                            else:
                                for version in sorted(
                                    existingVersions, key=lambda x: x["version"], reverse=True
                                ):
                                    name = version["version"]
                                    actV = QAction(name, sm)
                                    actV.triggered.connect(
                                        lambda y=None, v=version["version"]: sm.publish(
                                            executeState=True, useVersion=v
                                        )
                                    )
                                    menuExecuteV.addAction(actV)

                    if menuExecuteV.isEmpty():
                        menuExecuteV.setEnabled(False)

                    # Check if it is Image Render #
                    # Cambiado para soportar los renderclasses de MH
                    if not parentState.ui.className in renderclasses:
                        menuExecuteV.setEnabled(False)
                    ###############################

                    if parentState is None or parentState.ui.className == "Folder":
                        createMenu = sm.getStateMenu(parentState=parentState)
                        rcmenu.addMenu(createMenu)

                    if sm.activeList == sm.tw_export:
                        if not sm.standalone:
                            rcmenu.addAction(actExecute)
                            rcmenu.addMenu(menuExecuteV)

                    if actSort:
                        rcmenu.addAction(actSort)

                    rcmenu.addAction(actCopy)
                    rcmenu.addAction(actPaste)
                    rcmenu.addAction(actRename)
                    rcmenu.addAction(actDel)

                    rcmenu.exec_(sm.activeList.mapToGlobal(pos))

                    # after the function runs we turn the variable off to always run the original function.
                    self.isMHrendClass = False
                else:
                    # Call original Function
                    self.core.plugins.callUnpatchedFunction(sm.rclTree, pos, activeList)
                    
    @err_catcher(name=__name__)
    def getVersionStackContextFromPath(self, filepath):
        context = self.core.paths.getCachePathData(filepath)
        if "asset_path" in context:
            context["asset"] = os.path.basename(context["asset_path"])

        if "version" in context:
            del context["version"]
        if "comment" in context:
            del context["comment"]
        if "user" in context:
            del context["user"]
        
        # Bruteforce correct bug that wont let shotcam get versions
        if "\\" in context["product"]:
            context["product"] = context["product"].split("\\")[0]

        return context
    
    # @err_catcher(name=__name__)
    # def on_sm_import_importToApp(self, origin, doImport, update, impFileName):
    #     print("importing to app")
    #     self.fusFunctions.sm_import_importToApp(origin, doImport, update, impFileName)
        
    
    @err_catcher(name=__name__)
    def sm_playblast_createPlayblast(self, origin, jobFrames, outputName):
        ####################  MONKEYPATCHED  ######################
        #We get the view layer for the current context as default
        #Then we try to get what is the view layer for the current window.
        #This could be easily combined with the next block but I prefer it like this to see whats monkeypatched
        import bpy

        view_layer = bpy.context.view_layer
        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == 'VIEW_3D':
                    view_layer = window.view_layer
                    # print("Active view layer:", view_layer.name)
                    break
        ###########################################################

        renderAnim = jobFrames[0] != jobFrames[1]
        if origin.curCam is not None:
            bpy.context.scene.camera = bpy.context.scene.objects[origin.curCam]
            for window in bpy.context.window_manager.windows:
                screen = window.screen
                for area in screen.areas:
                    if area.type == "VIEW_3D":
                        area.spaces[0].region_3d.view_perspective = "CAMERA"
                        break

        prevRange = [bpy.context.scene.frame_start, bpy.context.scene.frame_end]
        prevRes = [
            bpy.context.scene.render.resolution_x,
            bpy.context.scene.render.resolution_y,
            bpy.context.scene.render.resolution_percentage,
        ]
        prevOutput = [
            bpy.context.scene.render.filepath,
            bpy.context.scene.render.image_settings.file_format,
        ]

        bpy.context.scene.frame_start = jobFrames[0]
        bpy.context.scene.frame_end = jobFrames[1]

        if origin.chb_resOverride.isChecked():
            bpy.context.scene.render.resolution_x = origin.sp_resWidth.value()
            bpy.context.scene.render.resolution_y = origin.sp_resHeight.value()
            bpy.context.scene.render.resolution_percentage = 100

        bpy.context.scene.render.filepath = os.path.normpath(outputName)
        base, ext = os.path.splitext(outputName)
        if ext == ".jpg":
            bpy.context.scene.render.image_settings.file_format = "JPEG"
        if ext == ".mp4":
            bpy.context.scene.render.image_settings.file_format = "FFMPEG"
            bpy.context.scene.render.ffmpeg.format = "MPEG4"
            bpy.context.scene.render.ffmpeg.audio_codec = "MP3"

        ####################  MONKEYPATCHED  ######################        
        #Instead of getting the override context as is, we inject the actual current Layer if possible.

        ctx = self.core.appPlugin.getOverrideContext(origin)
        ctx['view_layer'] = view_layer
        if bpy.app.version < (4, 0, 0):
            bpy.ops.render.opengl(
                ctx, animation=renderAnim, write_still=True, view_context=True)
        else:
            with bpy.context.temp_override(**ctx):
                bpy.ops.render.opengl(animation=renderAnim, write_still=True)

        ###############################################################

        bpy.context.scene.frame_start = prevRange[0]
        bpy.context.scene.frame_end = prevRange[1]
        bpy.context.scene.render.resolution_x = prevRes[0]
        bpy.context.scene.render.resolution_y = prevRes[1]
        bpy.context.scene.render.resolution_percentage = prevRes[2]
        bpy.context.scene.render.filepath = prevOutput[0]
        bpy.context.scene.render.image_settings.file_format = prevOutput[1]
