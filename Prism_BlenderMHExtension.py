# Blender Extension for internal use in Magic Hammer Studios

name = "MHBlenderExtension"
classname = "MHBlenderExtension"


import os
import sys
import traceback
import logging

from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *


from PrismUtils.Decorators import err_catcher

logger = logging.getLogger(__name__)

dirnm = os.path.dirname(__file__)
extra_paths = [os.path.abspath(os.path.join(dirnm, 'StateManagerNodes')), os.path.abspath(os.path.join(dirnm, 'StateManagerNodes', 'StateUserInterfaces'))]
for extra_path in extra_paths:
    if extra_path not in sys.path:
        sys.path.append(extra_path)


class MHBlenderExtension:
    def __init__(self, core):
        self.core = core
        self.version = "v0.0.1"
        self.functions = None
        self.monkeypatchedsm = None
        self.customstates = ["bld_MHRender", "bld_MHrendLayer"]
        self.isMHrendClass = False
                
        self.core.registerCallback("onStateManagerOpen", self.onStateManagerOpen, plugin=self)
        self.core.registerCallback("pluginLoaded", self.onPluginLoaded, plugin=self)

    @err_catcher(name=__name__)
    def onStateManagerOpen(self, origin):
        for customstate in self.customstates:
            if self.core.appPlugin.appShortName.lower() == "bld":
                self.monkeypatchedsm = origin
                #
                self.core.plugins.monkeyPatch(origin.rclTree, self.rclTree, self, force=True)
                self.core.plugins.monkeyPatch(self.core.mediaProducts.getMediaVersionInfoPathFromFilepath, self.getMediaVersionInfoPathFromFilepath, self, force=True)
                self.core.plugins.monkeyPatch(self.core.mediaProducts.getRenderProductDataFromFilepath, self.getRenderProductDataFromFilepath, self, force=True)
                #
                self.stateTypeCreator(customstate, origin)
                
    @err_catcher(name=__name__)
    def onPluginLoaded(self, plugin):
        if not self.functions:
            if self.core.appPlugin.appShortName.lower() == "bld":
                import Prism_BlenderMHExtension_Functions
                self.functions = Prism_BlenderMHExtension_Functions.Prism_BlenderMHExtension_Functions(self.core, self.core.appPlugin)
                # self.applyPatch(plugin)

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
    @err_catcher(name=__name__)
    def getMediaVersionInfoPathFromFilepath(self, path, mediaType=None):
        if self.isMHrendClass:
            print(":: monkeypatched getMediaVersionInfoPathFromFilepath ::")
            if mediaType == "playblasts":
                return self.getPlayblastVersionInfoPathFromFilepath(path)
            elif mediaType == "2drenders":
                return self.get2dVersionInfoPathFromFilepath(path)

            infoPath = os.path.join(
                # THIS IS THE PART WE PATCH, It should only go back one directory, not 2.
                os.path.dirname(path),
                "versioninfo" + self.core.configs.getProjectExtension(),
            )
            return infoPath
        else:
            # Call original function
            return self.core.plugins.callUnpatchedFunction(self.core.mediaProducts.getMediaVersionInfoPathFromFilepath, path, mediaType)
    
    @err_catcher(name=__name__)
    def getRenderProductDataFromFilepath(self, filepath, mediaType="3drenders"):
        if self.isMHrendClass:
            print(":: monkeypatched getRenderProductDataFromFilepath ::")
            entityType = self.core.paths.getEntityTypeFromPath(filepath)
            if entityType == "asset":
                key = "renderFilesAssets"
            elif entityType == "shot":
                key = "renderFilesShots"
            else:
                return {}

            context = {"type": entityType}
            context["mediaType"] = mediaType
            location = self.core.mediaProducts.getLocationFromPath(filepath)
            if location:
                context["project_path"] = self.core.paths.getRenderProductBasePaths()[location]

            template = self.core.projects.getResolvedProjectStructurePath(key, context=context)
            # THIS IS THE PART WE PATCH, it should have no aov part in the template.
            template = template.replace("@aov@", "")
            context = {"entityType": entityType, "project_path": context["project_path"]}
            data = self.core.projects.extractKeysFromPath(filepath, template, context=context)
            if not data:
                if entityType == "asset":
                    key = "playblastFilesAssets"
                elif entityType == "shot":
                    key = "playblastFilesShots"

                context = {"entityType": entityType, "project_path": context["project_path"]}
                template = self.core.projects.getResolvedProjectStructurePath(key, context=context)
                context = {"entityType": entityType, "project_path": context["project_path"]}
                data = self.core.projects.extractKeysFromPath(filepath, template, context=context)

            data["type"] = entityType
            if "asset_path" in data:
                data["asset"] = os.path.basename(data["asset_path"])

            return data
        else:
            # Call original function
            return self.core.plugins.callUnpatchedFunction(self.core.mediaProducts.getRenderProductDataFromFilepath, filepath, mediaType)
    
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
                    print("se usa patched")
                    rcmenu = QMenu(sm)
                    sm.rClickedItem = parentState

                    actExecute = QAction("Execute", sm)
                    actExecute.triggered.connect(lambda: sm.publish(executeState=True))

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
                                    outPath
                                )
                            elif "playblast" in parentState.ui.className.lower():
                                existingVersions = sm.core.mediaProducts.getVersionsFromSameVersionStack(
                                    outPath, mediaType="playblasts"
                                )
                            else:
                                existingVersions = sm.core.products.getVersionsFromSameVersionStack(
                                    outPath
                                )
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