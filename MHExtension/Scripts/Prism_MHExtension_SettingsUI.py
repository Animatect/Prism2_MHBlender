#   SettingsUI Dialog for the extension.
import os
import sys
import traceback
import logging

from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *


def userSettings_loadUI(plugin, origin):      #   ADDING "ResolveShortcuts" TO SETTINGS
        fusionExamplePath = os.path.join(
                                os.environ["appdata"], "Blackmagic Design", "Fusion"
                        )
        # Create a Widget
        origin.w_MHExtension = QWidget()
        lo_MHExtension = QVBoxLayout(origin.w_MHExtension)

        origin.w_MHExtension.setLayout(lo_MHExtension)

        lo_MHExtension.addItem(QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Fixed))

        # ENABLE FUSION FUNCTIONS
        lo_topBar = QHBoxLayout()

        plugin.chb_enableMHExtensionFusionFunctions = QCheckBox("Enable Fusion Extension Functions")
        lo_topBar.addWidget(plugin.chb_enableMHExtensionFusionFunctions)

        lo_topBar.addItem(QSpacerItem(20, 10, QSizePolicy.Expanding, QSizePolicy.Minimum))

        l_FusionSet = QLabel("Set Fusion Functions:")
        lo_topBar.addWidget(l_FusionSet)

        plugin.l_FusionStatus = QLabel("NOT SET    ")
        lo_topBar.addWidget(plugin.l_FusionStatus)

        plugin.but_setFusion = QPushButton("Set    ")
        plugin.but_setFusion.clicked.connect(setFusion)
        lo_topBar.addWidget(plugin.but_setFusion)

        plugin.but_removeFusionFunctions = QPushButton("Remove")
        plugin.but_removeFusionFunctions.clicked.connect(removeFusionFunctions)
        lo_topBar.addWidget(plugin.but_removeFusionFunctions)

        lo_topBar.addItem(QSpacerItem(60, 10, QSizePolicy.Fixed, QSizePolicy.Minimum))

        lo_MHExtension.addLayout(lo_topBar)

        # FUSION CONFIG GROUP BOX
        plugin.gb_FusionConfig = QGroupBox()
        lo_FusionConfig = QVBoxLayout(plugin.gb_FusionConfig)

        # FUSION INSTALL DIR SECTION
        l_FusionExecutable = QLabel("DaVinci Resolve executable:")
        lo_FusionConfig.addWidget(l_FusionExecutable)

        lo_FusionDir = QHBoxLayout()
        plugin.e_FusionDir = QLineEdit()
        lo_FusionDir.addWidget(plugin.e_FusionDir)

        but_browseFusionDir = QPushButton("Browse")
        but_browseFusionDir.clicked.connect(lambda: plugin.browseFiles(target=plugin.e_FusionDir,
                                                                        type="file",
                                                                        title="Select the Resolve Executable"
                                                                        ))
        lo_FusionDir.addWidget(but_browseFusionDir)
        lo_FusionConfig.addLayout(lo_FusionDir)

        l_FusionExample = QLabel(f"             (example:  {os.path.normpath(fusionExamplePath)}")
        l_FusionExample.setStyleSheet("font-size: 8pt;")
        lo_FusionConfig.addWidget(l_FusionExample)


        lo_FusionConfig.addItem(QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Fixed))



        #   TOOLTIPS
        tip = "Globally enable the Resolve Shortcuts functionality."
        plugin.chb_enableMHExtensionFusionFunctions.setToolTip(tip)

        tip = ("Status of the system environment variable (PRISM_DVR_SHORTCUTS_PATH).\n"
                "The enviro variable must be set to use the shortcut functions.\n\n"
                "To manually set via Prism enviroment or system:\n\n"
                "KEY:        'PRISM_DVR_SHORTCUTS_PATH'\n"
                "VALUE:    '[path/to/ResolveShortcuts] plugin dir'")
        l_FusionSet.setToolTip(tip)
        plugin.l_FusionStatus.setToolTip(tip)

        tip = ("Add the required system environment variable.\n"
                "Prism will automatically exit and must be manually restarted.")
        plugin.but_setFusion.setToolTip(tip)

        tip = ("Remove the system environment variable.\n"
                "Prism will automatically exit and must be manually restarted.")
        plugin.but_removeFusionFunctions.setToolTip(tip)

        tip = ("Location of Davinci Resolve's main executable.\n\n"
                "Should be automantically set during plugin load.")
        l_FusionExecutable.setToolTip(tip)
        plugin.e_FusionDir.setToolTip(tip)
        but_browseFusionDir.setToolTip(tip)

        tip = ("Location of the Resolve API script that is included\n"
                "with Davinci Resolve.\n"
                "(DaVinciResolveScript.py)\n\n"
                "Should be automantically set during plugin load.")


        origin.addTab(origin.w_MHExtension, "MH Prism Extension")

def setFusion():
        pass

def removeFusionFunctions():
        pass