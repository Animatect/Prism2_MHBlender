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
        self.customstates = ["bld_MHRender", "bld_MHrendLayer"]

        # # check if Blender plugin is loaded
        # blPlugin = self.core.getPlugin("Blender")
        # if blPlugin:
        #     # if yes, patch the function
        #     print("se cargó el plugin de blender para monkeypatch")
        #     self.applyPatch(blPlugin)
        
        self.core.registerCallback("onStateManagerOpen", self.onStateManagerOpen, plugin=self)
        self.core.registerCallback("pluginLoaded", self.onPluginLoaded, plugin=self)

    @err_catcher(name=__name__)
    def onStateManagerOpen(self, origin):
        for customstate in self.customstates:
            if self.core.appPlugin.appShortName.lower() == "bld":
                self.stateTypeCreator(customstate, origin)
    
    @err_catcher(name=__name__)
    def onPluginLoaded(self, plugin):
        if not self.functions:
            if self.core.appPlugin.appShortName.lower() == "bld":
                import Prism_BlenderMHExtension_Functions
                self.functions = Prism_BlenderMHExtension_Functions.Prism_BlenderMHExtension_Functions(self.core, self.core.appPlugin)
                # self.applyPatch(plugin)

    # We piggybag in a function called by the state manager when a state is enabled/disabled
    # @err_catcher(name=__name__)
    # def applyPatch(self, plugin):
    #     self.core.plugins.monkeyPatch(plugin.sm_saveStates, self.sm_saveStates, self, force=True)

    # @err_catcher(name=__name__)
    # def sm_saveStates(self, *args, **kwargs):
    #     self.core.plugins.callUnpatchedFunction(self.core.appPlugin.sm_saveStates, *args, **kwargs)
    #     # check if pass nodes should be disabled
    #     sm = args[0]
    #     for i in range(sm.tw_export.topLevelItemCount()):
    #         item = sm.tw_export.topLevelItem(i)
    #         if item.checkState(0) == Qt.Checked:
    #             item.ui.sm_toggleLayerNodes(toggle=item.text(0).endswith(" - disabled"))
    ### MonkeyPatch ends.

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


