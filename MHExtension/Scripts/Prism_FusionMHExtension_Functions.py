import os
import sys
import logging
import types

from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *

# if eval(os.getenv("PRISM_DEBUG", "False")):
# 	try:
# 		del sys.modules["widget_import_scenedata"]
# 	except:
# 		pass

# import widget_import_scenedata
from PrismUtils.Decorators import err_catcher as err_catcher

logger = logging.getLogger(__name__)	

class Prism_FusionMHExtension_Functions(object):
	def __init__(self, core, plugin):
		self.core = core
		self.plugin = plugin
		self.appplugin = self.core.appPlugin

		# Dynamically add importBlenderCam as a method to self.appplugin
		self.appplugin.importBlenderCam = types.MethodType(self.importBlenderCam, self.core.appPlugin)

	@err_catcher(name=__name__)
	def sm_extendFusionPlugin(self, origin):
		if self.appplugin.legacyImportHandlers:
			legacyImportHandlers:dict = self.appplugin.legacyImportHandlers
			if not legacyImportHandlers.get(".bcam"):
				legacyImportHandlers[".bcam"] = {"importFunction": self.importBlenderCam}
	

	@err_catcher(name=__name__)
	def importBlenderCam(self, Filepath, origin) -> bool:
		comp = self.appplugin.getCurrentComp()
		flow = comp.CurrentFrame.FlowView

		from MH_BlenderCam_Fusion_Importer import BlenderCameraImporter
		BcamImporter = BlenderCameraImporter()
		
		#   Deselect All
		flow.Select()

		BcamImporter.import_blender_camera(Filepath)
		if len(comp.GetToolList(True)) > 0:
			return True
		else:
			return False
		
	#	This imports shotcams as a legacy
	@err_catcher(name=__name__)
	def shotCam(self):
		logger.debug("Loading state manager patched function: 'shotCam', patched by the MHExtension.")
		if self.appplugin.sm_checkCorrectComp(self.appplugin.getCurrentComp()):
			sm = self.appplugin.MP_stateManager

		sm.saveEnabled = False
		for i in sm.states:
			if i.ui.className == "Legacy3D_Import" and i.ui.taskName == "ShotCam":
				mCamState = i.ui
				camState = i

		if "mCamState" in locals():
			mCamState.importLatest()
			sm.selectState(camState)
		else:
			fileName = sm.core.getCurrentFileName()
			fnameData = sm.core.getScenefileData(fileName)
			if not (
				os.path.exists(fileName)
				and sm.core.fileInPipeline(fileName)
			):
				sm.core.showFileNotInProjectWarning(title="Warning")
				sm.saveEnabled = True
				return False

			if fnameData.get("type") != "shot":
				msgStr = "Shotcams are not supported for assets."
				sm.core.popup(msgStr)
				sm.saveEnabled = True
				return False

			if sm.core.getConfig("globals", "productTasks", config="project"):
				fnameData["department"] = os.getenv("PRISM_SHOTCAM_DEPARTMENT", "Layout")
				fnameData["task"] = os.getenv("PRISM_SHOTCAM_TASK", "Cameras")

			filepath = sm.core.products.getLatestVersionpathFromProduct(
				"_ShotCam", entity=fnameData
			)
			
			if not filepath:
				sm.core.popup("Could not find a shotcam for the current shot.")
				sm.saveEnabled = True
				return False
			
			#####
			
			# BlenderCam Check
			root, _ = os.path.splitext(filepath)
			new_file_path = os.path.normpath(root + '.bcam')
			if os.path.exists(new_file_path):
				filepath = new_file_path

			#####
			sm.createState("Legacy3D_Import", importPath=filepath, setActive=True)

		sm.setListActive(sm.tw_import)
		sm.activateWindow()
		sm.activeList.setFocus()
		sm.saveEnabled = True
		sm.saveStatesToScene()
