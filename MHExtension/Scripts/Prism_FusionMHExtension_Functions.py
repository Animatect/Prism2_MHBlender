import os
import sys
import logging

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

	@err_catcher(name=__name__)
	def sm_import_importToApp(self, origin, doImport, update, impFileName):
		# Check if a .bcam file exists, if so, prefer it over the abc, this means a Mh blender camera.
		plugin = self.appplugin
		root, _ = os.path.splitext(impFileName)
		isbcam = False
		new_file_path = os.path.normpath(root + '.bcam')
		if os.path.exists(new_file_path):
			isbcam = True
			impFileName = new_file_path
		
		comp = plugin.getCurrentComp()
		flow = comp.CurrentFrame.FlowView
		fileName = os.path.splitext(os.path.basename(impFileName))
		origin.setName = ""
		result = False
		# Check that we are not importing in a comp different than the one we started the stateManager from
		if plugin.sm_checkCorrectComp(comp):
			#try to get an active tool to set a ref position
			activetool = None
			try:
				activetool = comp.ActiveTool()
			except:
				pass
			if activetool and not activetool.GetAttrs("TOOLS_RegID") =="BezierSpline":
				atx, aty = flow.GetPosTable(activetool).values()
			else:
				atx, aty = plugin.find_LastClickPosition()
			
			#get Extension
			ext = fileName[1].lower()

			#if extension is supported
			if ext in plugin.importHandlers:
				# Do the importing
				result = plugin.importHandlers[ext]["importFunction"](impFileName, origin)
			else:
				plugin.core.popup("Format is not supported.")
				return {"result": False, "doImport": doImport}

			#After import update the stateManager interface
			if result:
				#check if there was a merge3D in the import and where was it connected to
				newNodes = [n.Name for n in comp.GetToolList(True).values()]
				if isbcam:
					importedNodes = []
					importedNodes.append(plugin.getNode(newNodes[0]))
					origin.setName = "Import_" + fileName[0]			
					origin.nodes = importedNodes
				else:
					refPosNode, positionedNodes = plugin.ReplaceBeforeImport(origin, newNodes)
					plugin.cleanbeforeImport(origin)
					if refPosNode:
						atx, aty = flow.GetPosTable(refPosNode).values()
			
					importedTools = comp.GetToolList(True).values()
					#Set the position of the imported nodes relative to the previously active tool or last click in compView
					impnodes = [n for n in importedTools]
					if len(impnodes) > 0:
						comp.Lock()

						fisrtnode = impnodes[0]
						fstnx, fstny = flow.GetPosTable(fisrtnode).values()

						for n in impnodes:
							if not n.Name in positionedNodes:
								x,y  = flow.GetPosTable(n).values()

								offset = [x-fstnx,y-fstny]
								newx = x+(atx-x)+offset[0]
								newy = y+(aty-y)+offset[1]
								flow.SetPos(n, newx-1, newy)

						comp.Unlock()
					##########

					importedNodes = []
					for i in newNodes:
						# Append sufix to objNames to identify product with unique Name
						node = plugin.getObject(i)
						newName = plugin.applyProductSufix(i, origin)
						node.SetAttrs({"TOOLS_Name":newName, "TOOLB_NameSet": True})
						importedNodes.append(plugin.getNode(newName))

					origin.setName = "Import_" + fileName[0]			
					origin.nodes = importedNodes

				#Deselect All
				flow.Select()

				objs = [plugin.getObject(x) for x in importedNodes]
				
				#select nodes in comp
				for o in objs:
					flow.Select(o)

				#Set result to True if we have nodes
				result = len(importedNodes) > 0

		return {"result": result, "doImport": doImport}
