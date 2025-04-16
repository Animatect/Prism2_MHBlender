#   SettingsUI Dialog for the extension.
import os
import sys
import traceback
import logging
import shutil

from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *

from PrismUtils.Decorators import err_catcher_plugin as err_catcher

logger = logging.getLogger(__name__)

class Prism_MHExtension_Integration(object):
	def __init__(self, core, plugin):
		self.core = core
		self.plugin = plugin
		self.scripts = [
			"BlenderOCIOmanager.py",
			"MH_AbsoluteToPathMaps.py",
			"MH_PathMapsToAbsolute.py",
			"MH_PrismShotSwitcher.py",
		]
		self.configs = [
			"MHMenu.fu",
		]		
		self.presetprj = [
			"CGNOVADefault",
		]

	@err_catcher(name=__name__)
	def userSettings_loadUI(self, origin):  # ADDING "Integrations" TO SETTINGS
		fusionExamplePath = os.path.join(
			os.environ["appdata"], "Blackmagic Design", "Fusion"
		)
		# Create a Widget
		origin.w_MHExtension = QWidget()
		lo_MHExtension = QVBoxLayout(origin.w_MHExtension)
		lo_MHExtension.setSpacing(10)  # Reduce spacing between items
		lo_MHExtension.setContentsMargins(10, 10, 10, 10)  # Add consistent margins

		origin.w_MHExtension.setLayout(lo_MHExtension)

		# FUSION CONFIG GROUP BOX
		self.gb_FusionConfig = QGroupBox()
		self.gb_FusionConfig.setTitle("Fusion Configuration")  # Add a title for clarity
		lo_FusionConfig = QVBoxLayout(self.gb_FusionConfig)
		lo_FusionConfig.setSpacing(5)  # Reduce spacing between elements in the group box
		lo_FusionConfig.setContentsMargins(10, 10, 10, 10)  # Add consistent margins

		# FUSION INSTALL DIR SECTION
		l_FusionInstallDir = QLabel("Fusion Install Dir")
		lo_FusionConfig.addWidget(l_FusionInstallDir)

		lo_FusionDir = QHBoxLayout()
		self.e_FusionDir = QLineEdit()
		lo_FusionDir.addWidget(self.e_FusionDir)

		# but_browseFusionDir = QPushButton("Browse")
		# but_browseFusionDir.setToolTip("Click to select the Fusion Install dir.")
		# but_browseFusionDir.clicked.connect(lambda: self.browseFusionFiles(
		# 	fusionExamplePath=fusionExamplePath,
		# 	target=self.e_FusionDir,
		# 	type="file",
		# 	title="Select the Fusion install dir."
		# ))
		# lo_FusionDir.addWidget(but_browseFusionDir)
		lo_FusionConfig.addLayout(lo_FusionDir)

		l_FusionExample = QLabel(f"             (example:  {os.path.normpath(fusionExamplePath)}")
		l_FusionExample.setStyleSheet("font-size: 8pt;")
		lo_FusionConfig.addWidget(l_FusionExample)

		# Add and Remove Buttons Section
		lo_ButtonRow = QHBoxLayout()  # Create a horizontal layout for the buttons
		lo_ButtonRow.addStretch()  # Add a stretchable space to push buttons to the right

		self.but_add = QPushButton("Add")
		self.but_add.clicked.connect(lambda: self.browseFusionFiles(
			fusionExamplePath=fusionExamplePath,
			target=self.e_FusionDir,
			type="file",
			title="Select the Fusion install dir."
		))
		self.but_add.setToolTip("Click to add a new Fusion configuration entry.")
		lo_ButtonRow.addWidget(self.but_add)

		self.but_remove = QPushButton("Remove")
		self.but_remove.clicked.connect(lambda: self.onRemoveFusion(
			installPath=os.path.normpath(self.e_FusionDir.text()),
			target=self.e_FusionDir
		))
		self.but_remove.setToolTip("Click to remove the selected Fusion configuration entry.")
		lo_ButtonRow.addWidget(self.but_remove)

		lo_FusionConfig.addLayout(lo_ButtonRow)  # Add the button layout to the group box layout

		lo_FusionConfig.addItem(QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Fixed))

		lo_MHExtension.addWidget(self.gb_FusionConfig, alignment=Qt.AlignTop)  # Add group box with alignment
		
		#############################################
		# ADD Presets
		# PPRESETS CONFIG GROUP BOX
		self.gb_PresetsConfig = QGroupBox()
		self.gb_PresetsConfig.setTitle("Presets Configuration")  # Add a title for clarity
		lo_PresetsConfig = QVBoxLayout(self.gb_PresetsConfig)
		lo_PresetsConfig.setSpacing(5)  # Reduce spacing between elements in the group box
		lo_PresetsConfig.setContentsMargins(10, 10, 10, 10)  # Add consistent margins

		# Button Section
		lo_presetsButtonRow = QHBoxLayout()  # Create a horizontal layout for the buttons
		# lo_presetsButtonRow.addStretch()  # Add a stretchable space to push buttons to the right

		self.but_presetsAdd = QPushButton("Add")
		self.but_presetsAdd.clicked.connect(self.addPresets)
		self.but_presetsAdd.setToolTip("Click to add MH Preferences.")
		lo_presetsButtonRow.addWidget(self.but_presetsAdd)

		self.but_presetsOpen = QPushButton("Open Presets Folder")
		self.but_presetsOpen.clicked.connect(self.OpenPresets)
		self.but_presetsOpen.setToolTip("Click to add MH Preferences.")
		lo_presetsButtonRow.addWidget(self.but_presetsOpen)

		lo_presetsButtonRow.addStretch()  # Add a stretchable space to push buttons to the right
		
		lo_PresetsConfig.addLayout(lo_presetsButtonRow)  # Add the button layout to the group box layout
		lo_MHExtension.addWidget(self.gb_PresetsConfig, alignment=Qt.AlignTop)  # Add group box with alignment


		############################################

		# ADD MENU ENTRY TO SETTINGS UI
		origin.addTab(origin.w_MHExtension, "MH Prism Extension")

	@err_catcher(name=__name__)
	def browseFusionFiles(self, fusionExamplePath, target, type='file', title='Select File or Folder'):
		# Check if fusionExamplePath exists
		default_path = fusionExamplePath if os.path.exists(fusionExamplePath) else os.path.expanduser("~")
		
		# Open a file dialog to select a directory
		folder = QFileDialog.getExistingDirectory(
			None,
			"Select Fusion Installation Directory",
			default_path,
			QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
		)
		
		# If a folder is selected, update the QLineEdit
		if folder:
			target.setText(folder)
			installed = self.addFusion(folder)
			if installed:
				self.core.popup("Instalation was successful", title="Fusion Extras Instalation", severity="info")
			else:
				
				self.core.popup("Instalation Failed", title="Fusion Extras Instalation", severity="Warning")
	
	@err_catcher(name=__name__)			
	def onRemoveFusion(self, installPath, target):
		uninstalled = self.removeFusion(installPath)
		if uninstalled:
				target.setText("")
				self.core.popup("Deinstalation was successful", title="Fusion Extras Instalation", severity="info")
		else:
			
			self.core.popup("Deinstalation Failed", title="Fusion Extras Instalation", severity="Warning")

		
	@err_catcher(name=__name__)
	def addFusion(self, installPath):
		scripts = self.scripts.copy()
		configs = self.configs.copy()
		
		if not os.path.exists(installPath):
			QMessageBox.warning(
				self.core.messageParent,
				"MH Integration",
				"Invalid Fusion path: %s.\nThe path doesn't exist." % installPath,
				QMessageBox.Ok,
			)
			return False
		
		integrationBase = os.path.join(
			os.path.dirname(os.path.dirname(__file__)), "Integrations", "Fusion"
		)
		addedFiles = []
		try:
			for i in configs:
				origFile = os.path.normpath(os.path.join(integrationBase, i))
				targetFile = os.path.normpath(os.path.join(installPath, "Config", i))

				if not os.path.exists(os.path.dirname(targetFile)):
					os.makedirs(os.path.dirname(targetFile))
					addedFiles.append(os.path.dirname(targetFile))

				if os.path.exists(targetFile):
					os.remove(targetFile)

				shutil.copy2(origFile, targetFile)
				addedFiles.append(targetFile)


			for i in scripts:
				file_name, file_extension = os.path.splitext(i)
				origFile = os.path.join(integrationBase, i)
				targetFile = os.path.join(installPath, "Scripts", "MH", i)

				if not os.path.exists(os.path.dirname(targetFile)):
					os.makedirs(os.path.dirname(targetFile))
					addedFiles.append(os.path.dirname(targetFile))

				if os.path.exists(targetFile):
					os.remove(targetFile)

				shutil.copy2(origFile, targetFile)
				addedFiles.append(targetFile)
			return True
		except Exception as e:
			exc_type, exc_obj, exc_tb = sys.exc_info()

			msgStr = (
				"Errors occurred during the removal of the Fusion integration.\n\n%s\n%s\n%s"
				% (str(e), exc_type, exc_tb.tb_lineno)
			)
			msgStr += "\n\nRunning this application as administrator could solve this problem eventually."

			QMessageBox.warning(self.core.messageParent,"Prism Integration", msgStr)

			return False

	@err_catcher(name=__name__)			
	def removeFusion(self, installPath):
		try:
			pFiles = []
			for i in self.configs:
				pFiles.append(
					os.path.join(installPath, "Config", i)
				)

			for file in self.scripts:
				pFiles.append(
					os.path.join(
						installPath, "Scripts", "MH", file
					)
				)

			for i in pFiles:
				if os.path.exists(i):
					os.remove(i)

			pfolder = os.path.join(installPath, "Scripts", "MH")
			if not os.listdir(pfolder):
				os.rmdir(pfolder)
			
			return True

		except Exception as e:
			exc_type, exc_obj, exc_tb = sys.exc_info()

			msgStr = (
				"Errors occurred during the removal of the Fusion integration.\n\n%s\n%s\n%s"
				% (str(e), exc_type, exc_tb.tb_lineno)
			)
			msgStr += "\n\nRunning this application as administrator could solve this problem eventually."

			QMessageBox.warning(self.core.messageParent,
								"Prism Integration", msgStr)
			return False

	@err_catcher(name=__name__)
	def addPresets(self):
		# PresetProjects
		msj = "PresetProjects: \n"
		integrationBase = os.path.join(
			os.path.dirname(os.path.dirname(__file__)), "Integrations", "Presets", "Projects"
		)
		baseTargetDir = os.path.join(os.path.dirname(self.core.getUserPrefConfigPath()), "Presets", "Projects")
		for i in self.presetprj:
			targetDir = os.path.join(baseTargetDir, i)
			if not os.path.exists(os.path.dirname(baseTargetDir)):
				os.makedirs(os.path.dirname(baseTargetDir))

			if os.path.exists(targetDir):
				os.remove(targetDir)

			shutil.copytree(os.path.join(integrationBase, i), targetDir)
			msj += i +"\n"
		msj += f"\nWere installed at:\n{baseTargetDir}"
		self.core.popup(msj, title="Preset Projects Instalation", severity="info")

		return True

	@err_catcher(name=__name__)
	def OpenPresets(self):
		baseTargetDir = os.path.join(os.path.dirname(self.core.getUserPrefConfigPath()), "Presets")
		os.startfile(baseTargetDir)

	@err_catcher(name=__name__)
	def userSettings_saveSettings(self, origin, settings):
		try:
			if "MHExtension" not in settings:
				settings["MHExtension"] = {}

			settings["MHExtension"]["FusionDir"] = self.e_FusionDir.text()


		except Exception as e:
			logger.warning(f"ERROR: Could not save user settings:\n{e}")


	@err_catcher(name=__name__)
	def userSettings_loadSettings(self, origin, settings):
		print("LOADING ESTO")
		try:
			if "MHExtension" in settings:
				if "FusionDir" in settings["MHExtension"]:
					self.e_FusionDir.setText(settings["MHExtension"]["FusionDir"])

		except Exception as e:
			logger.warning(f"ERROR: Failed to load user settings:\n{e}")

