import os
import sys
import re
import uuid
import hashlib


def getPrismRoot():
	prismRoot = os.getenv("PRISM_ROOT")
	if not prismRoot:
		prismRoot = PRISMROOT
	return prismRoot
prismRoot = getPrismRoot()

scriptDir = os.path.join(prismRoot, "Scripts")
pysideDir = os.path.join(prismRoot, "PythonLibs", "Python3", "PySide")
sys.path.append(pysideDir)

if scriptDir not in sys.path:
	sys.path.append(scriptDir)

if pysideDir not in sys.path:
	sys.path.append(pysideDir)


import PrismCore

from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *

class LoadingScreen(QWidget):
	"""Temporary loading window before showing the main UI."""
	def __init__(self):
		super().__init__()
		self.setWindowTitle("Loading...")
		# self.setGeometry(100, 100, 200, 100)

		layout = QVBoxLayout()
		label = QLabel("Loading...", self)
		label.setAlignment(Qt.AlignCenter)
		layout.addWidget(label)

		self.setLayout(layout)
		self.adjustSize()  # Auto-adjust window size

class MyWindow(QWidget):
	"""Main Application Window."""
	def __init__(self, pcore):
		super().__init__()

		self.core = pcore
		self.setWindowTitle("MH Loader Shot Switcher")
		self.previewWidth = int(200 )
		self.previewHeight = int((200 ) / (16/9.0))
            
		# self.setMinimumWidth(350)

		self.core.registerCallback("onProjectChanged", self.onProjectChanged, plugin=self.core.appPlugin)

		self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)  # Always on top

		# **Main Layout**
		layout = QVBoxLayout()

		# **Top Bar Layout (Projects Button)**
		top_bar = QHBoxLayout()
		top_bar.addStretch()  # Push button to the right

		self.b_projects = QPushButton("Projects")
		top_bar.addWidget(self.b_projects)

		layout.addLayout(top_bar)

		# **Image**
		iconPath = os.path.join(
                self.core.prismRoot, "Scripts", "UserInterfacesPrism", "info.png"
            )
		self.l_preview = QLabel(self)
		self.emptypmapPrv = self.core.media.getFallbackPixmap()
		# pixmap = QPixmap("your_image.png")  # Replace with your image path
		# self.image_label.setPixmap(pixmap.scaledToWidth(200, Qt.SmoothTransformation))
		self.l_preview.setPixmap(self.emptypmapPrv)
		self.l_preview.setAlignment(Qt.AlignCenter)
		layout.addWidget(self.l_preview)

		

		# **Dropdown for Category Selection (Sequences)**
		self.label_sequence = QLabel("Sequences:")
		layout.addWidget(self.label_sequence)

		self.dd_sequences = QComboBox()
		self.dd_sequences.addItems([])
		self.dd_sequences.currentIndexChanged.connect(self.update_shots)
		layout.addWidget(self.dd_sequences)

		# **Dropdown for Dynamic Values (Shots)**
		self.label_shots = QLabel("Shots:")
		layout.addWidget(self.label_shots)

		self.dd_shots = QComboBox()
		layout.addWidget(self.dd_shots)

		# **Bottom Button**
		self.b_changePaths = QPushButton("Change Paths")
		layout.addWidget(self.b_changePaths)

		self.setLayout(layout)

		# **Auto-size window to fit contents**
		self.adjustSize()
		self.resize(350, 200)

		# Connections
		self.b_projects.clicked.connect(self.onProjectsClicked)
		self.b_changePaths.clicked.connect(self.onChangePathsClicked)

		self.refreshAsset()

	def getPreviewImage(self, load=True):
		image = None
		if load:
			configPath = self.core.getUserPrefConfigPath()
			prpath = self.core.projectPath
			# print("PROY: ", prpath)
			# print(configPath)
			if os.path.isfile(configPath):
				image = self.core.projects.getProjectImage(
					projectPath = self.core.projectPath
					# projectConfig = configPath
				)
				# print("image: ", image)
				if not image:
					imgFile = os.path.join(
						self.core.prismRoot,
						"Presets/Projects/Default/00_Pipeline/Fallbacks/noFileBig.jpg",
					)
					pixmap = self.core.media.getPixmapFromPath(imgFile)
					pixmap = self.core.media.scalePixmap(pixmap, self.previewWidth, self.previewHeight, keepRatio=True, fitIntoBounds=False, crop=True)
					return pixmap

		if load and image:
			pixmap = QPixmap(image)
			self.validPreview = pixmap
			pixmap = self.core.media.scalePixmap(pixmap, self.previewWidth, self.previewHeight, keepRatio=True, fitIntoBounds=False, crop=True)
		else:
			pixmap = "loading"

		return pixmap

	def refreshAsset(self):
		# **Populate Initial List**
		self.update_sequences()
		self.updatePreview()

	
	def updatePreview(self, load=True):
		if hasattr(self, "loadingGif"):
			self.loadingGif.setScaledSize(QSize(self.l_preview.width(), int(self.l_preview.width() / (300/169.0))))

		ppixmap = self.getPreviewImage(load=load)
		if not ppixmap or ppixmap == "loading":
			return

		self.l_preview.setPixmap(ppixmap)

	def update_sequences(self):
		sequences:list = []
		for sq in self.core.entities.getSequences():
			sequences.append(sq['sequence'])
		
		self.dd_sequences.clear()
		self.dd_sequences.addItems(sequences)
		self.update_shots()


	def update_shots(self):
		selected_sequence = self.dd_sequences.currentText()
		shots:list = []
		for sh in self.core.entities.getShotsFromSequence(selected_sequence):
			shots.append(sh["shot"])

		self.dd_shots.clear()
		self.dd_shots.addItems(shots)
		

	def onProjectsClicked(self, state=None):
		if hasattr(self, "w_projects") and self.w_projects.isVisible():
			self.w_projects.close()
			return

		if not hasattr(self, "w_projects"):
			self.w_projects = self.core.projects.ProjectListWidget(self)
			self.b_projects.setFocusProxy(self.w_projects)

		self.w_projects.showWidget()
		QApplication.processEvents()
	
	def onChangePathsClicked(self):
		comp = fusion.CurrentComp
		flow = comp.CurrentFrame.FlowView
		loaders = self.getSelectedTools(comp, toolType = "Loader")
		newStateUID = self.createUID()
		updatecount = 0
		errorcount = 0
		for tool in loaders:
			oldPath = tool.GetData('Prism_ToolData')['filepath']
			# print("oldPath: \n", oldPath)
			context = self.core.paths.getRenderProductData(oldPath)
			context["shot"] = self.dd_shots.currentText()
			context["sequence"] = self.dd_sequences.currentText()
			context["identifier"] = tool.GetData('Prism_ToolData')['mediaId']
			context["aov"] = tool.GetData('Prism_ToolData')['aov']
			context["extension"] = tool.GetData('Prism_ToolData')['extension']
			context["frame"] = "0001"
			hmv = self.core.mediaProducts.getHighestMediaVersion(context, getExisting=True)
			context["version"] = str(hmv)
			# print("CTX: \n", context)

			#Blender paths fix
			path:str = self.core.projects.getResolvedProjectStructurePath("renderFilesShots", context=context)
			dir_path, filename = os.path.split(path)
			new_basename = context["aov"]
			newPath:str = ""
			match = re.search(r"\.(\d+)\.(\w+)$", filename)
			#New Filename for Blender MH naming convention.
			if match:
				frame, extension = match.groups()
				# Build new filename and full path
				new_filename = f"{new_basename}.{frame}.{extension}"
				newPath = os.path.join(dir_path, new_filename)
			else:
				newPath =  path
			temppath = newPath
			#Taking buggy undercore naming into consideration.
			if not os.path.exists(temppath):
				# Replace the dot before frame number with underscore
				# e.g. Something.0001.exr -> Something_0001.exr
				temppath = re.sub(r'\.(\d+)\.(\w+)$', r'_\1.\2', temppath)
			if os.path.exists(temppath):
				newPath = temppath
			
			##############################
			#			SET IT			 #
			##############################
			if os.path.exists(newPath):
				#Set the new name.
				newNodeName = f"{context['sequence']}_{context['shot']}_{context['identifier']}_{context['aov']}_{context['version']}"
				tool.SetAttrs({"TOOLS_Name": newNodeName})

				#Assign the new path
				tool.Clip = newPath

				#Correct the prism data:
				newdata:dict = tool.GetData('Prism_ToolData').copy()
				newdata["stateUID"] = newStateUID
				newdata["nodeName"] = newNodeName
				newdata["version"] = context["version"]
				newdata["filepath"] = newPath
				newdata["sequence"] = context["sequence"]
				newdata["shot"] = context["shot"]
				# print("oldData: \n", tool.GetData('Prism_ToolData'))
				tool.SetData('Prism_ToolData', newdata)
				# print("newData: \n", tool.GetData('Prism_ToolData'))

				#Start and end duration#
				startfr, endfr = self.getStartFrAndDuration(newPath)

				tool.GlobalOut[0] = endfr
				tool.GlobalIn[0] = startfr

				tool.ClipTimeStart = 0
				tool.ClipTimeEnd = endfr - startfr

				tool.HoldFirstFrame = 0
				tool.HoldLastFrame = 0

				updatecount += 1
			
			else:
				tool.TileColor = { 'R': 1.0, 'G': 0.0, 'B': 0.0 }
				pos = flow.GetPosTable(tool)
				flow.SetPos(tool, pos[1]-0.5, pos[2])
				errorcount += 1
						
		self.popup(f"{updatecount} loaders paths found and updated.\n{errorcount} loaders errored out and were not modified.")

	
	def popup(self, msg:str):
		msg_box = QMessageBox(self)
		msg_box.setWindowTitle("Info")
		msg_box.setText(msg)
		msg_box.setIcon(QMessageBox.Information)  # Can be Information, Warning, Critical, etc.
		msg_box.setStandardButtons(QMessageBox.Ok)

		# Show the message box
		msg_box.exec()

	def getSelectedTools(self, comp, toolType:str=None) -> list:
		toolList = []
		for tool in comp.GetToolList(True).values():
			if toolType:
				if tool.GetAttrs("TOOLS_RegID") == toolType:
					toolList.append(tool)
			else:
				toolList.append(tool)

		return toolList
	def onProjectChanged(self, core):
		# curPrj = core.getConfig("globals", "current project")
		prstr = core.projects.getProjectStructure()
		# print(curPrj)
		# print("prch")
		print(core.projectPath)
		self.updatePreview()
		self.refreshAsset()

	def getStartFrAndDuration(self, baseFile):
		versionDir = os.path.dirname(baseFile)
		sources = self.core.media.getImgSources(versionDir, getFirstFile=True)

		# source = sources[0]
		sourcePath = os.path.join(versionDir, baseFile)
		if not os.path.isdir(sourcePath):
			sourceDir = os.path.dirname(sourcePath)
		else:
			sourceDir = sourcePath

		seqName, seqFiles = self.getSequenceData(sourceDir)
		startfr = self.core.media.getFrameRangeFromSequence(seqFiles, baseFile=baseFile)

		return startfr

	def getSequenceData(self, sourceDir):
		#   Handle
		if self.getLinkedFilepath(sourceDir):
			files = self.getLinkedFilepath(sourceDir)

		else:
			files = os.listdir(sourceDir)

		#   Filter and get sequence Dict
		validFiles = self.core.media.filterValidMediaFiles(files)
		validFiles = sorted(validFiles, key=lambda x: x if "cryptomatte" not in os.path.basename(x) else "zzz" + x)

		seqDict = self.core.media.detectSequences(validFiles)
		seqName, seqFiles = next(iter(seqDict.items()))

		return seqName, seqFiles
	
	def getLinkedFilepath(self, sourceDir):
		redirectFile = os.path.join(sourceDir, "REDIRECT.txt")
		if os.path.exists(redirectFile):
			with open(redirectFile, "r") as rdFile:
				files = [rdFile.read()]

			return files
		
		else:
			return None
	
	def createUID(self, length:int=8):
		uid = uuid.uuid4()
		# Create a SHA-256 hash of the UUID
		hashObject = hashlib.sha256(uid.bytes)
		# Convert the hash to a hex string and truncate it to the desired length
		shortUID = hashObject.hexdigest()[:length]

		return shortUID

def prismInit():
	pcore = PrismCore.create(app="Standalone", prismArgs=["noUI", "loadProject"])

	return pcore


def getIconPath():
	return os.path.join(getPrismRoot(), "Scripts", "UserInterfacesPrism", "p_tray.png")


if __name__ == "__main__":
	print("initing")
	qapp = QApplication.instance()
	if qapp == None:
		qapp = QApplication(sys.argv)
		loading_screen = LoadingScreen()
		loading_screen.show()
		core = prismInit()
		loading_screen.close()
		window = MyWindow(core)
		window.show()
	qapp.exec_()

	# WirelessNode.Input.ConnectTo(AutoDomainNode)
	# AutoDomainNodeName = WirelessNode.Input.GetConnectedOutput().GetTool().Name
	# 'TOOLS_RegID': 'Fuse.Wireless'
	# comp.AddTool("Fuse.Wireless")


	# Composition.MapPath(path)
	# Composition.ReverseMapPath(mapped)