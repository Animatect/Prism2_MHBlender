import os
import sys


def getPrismRoot():
	prismRoot = os.getenv("PRISM_ROOT")
	if not prismRoot:
		prismRoot = "C:/Program Files/Prism2"
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
		self.image_label = QLabel(self)
		pixmap = QPixmap("your_image.png")  # Replace with your image path
		self.image_label.setPixmap(pixmap.scaledToWidth(200, Qt.SmoothTransformation))
		self.image_label.setAlignment(Qt.AlignCenter)
		layout.addWidget(self.image_label)

		

		# **Dropdown for Category Selection (Sequences)**
		self.label_sequence = QLabel("Sequences:")
		layout.addWidget(self.label_sequence)

		self.dropdown_category = QComboBox()
		self.dropdown_category.addItems(["Fruits", "Vegetables", "Animals"])
		self.dropdown_category.currentIndexChanged.connect(self.update_list)
		layout.addWidget(self.dropdown_category)

		# **Dropdown for Dynamic Values (Shots)**
		self.label_shots = QLabel("Shots:")
		layout.addWidget(self.label_shots)

		self.dropdown_values = QComboBox()
		layout.addWidget(self.dropdown_values)

		# **Bottom Button**
		self.b_changePaths = QPushButton("Change Paths")
		layout.addWidget(self.b_changePaths)

		self.setLayout(layout)

		# **Auto-size window to fit contents**
		self.adjustSize()

		# **Populate Initial List**
		self.update_list()

		# Connections
		self.b_projects.clicked.connect(self.onProjectsClicked)
		self.b_changePaths.clicked.connect(self.onChangePathsClicked)

	def update_list(self):
		"""Update the second dropdown based on the selected category."""
		items = {
			"Fruits": ["Apple", "Banana", "Cherry"],
			"Vegetables": ["Carrot", "Broccoli", "Spinach"],
			"Animals": ["Dog", "Cat", "Elephant"]
		}

		selected_category = self.dropdown_category.currentText()
		self.dropdown_values.clear()
		self.dropdown_values.addItems(items.get(selected_category, []))

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
		# print("click")
		print(self.core.projectPath)
		for s in self.core.entities.getSequences():
			print(s['sequence'])
			print("shots")
			for s in self.core.entities.getShotsFromSequence(s['sequence']):
				print("		", s['shot'])
		print("\n")

	def onProjectChanged(self, core):
		# curPrj = core.getConfig("globals", "current project")
		prstr = core.projects.getProjectStructure()
		# print(curPrj)
		print("prch")
		print(core.projectPath)

def prismInit():
	pcore = PrismCore.create(app="Standalone", prismArgs=["noUI", "loadProject"])

	return pcore


def getIconPath():
	return os.path.join(getPrismRoot(), "Scripts", "UserInterfacesPrism", "p_tray.png")


if __name__ == "__main__":
	print("initing")
	# core = prismInit()
	# print(core.version)
	# print("sequences")
	# for s in core.entities.getSequences():
	# 	print(s['sequence'])
	# 	print("shots")
	# 	for s in core.entities.getShotsFromSequence(s['sequence']):
	# 		print("		", s['shot'])
	# print("\n")
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