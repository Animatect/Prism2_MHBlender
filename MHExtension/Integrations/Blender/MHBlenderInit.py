# -*- coding: utf-8 -*-
#
# MH Blender Extension Integration
# Adds custom MH_Ops panel to Blender's Prism panel category
#

import os
import sys

import bpy

# Get the Prism root from environment or placeholder
if "PRISM_ROOT" in os.environ:
    prismRoot = os.environ["PRISM_ROOT"]
    if not prismRoot:
        raise Exception("PRISM_ROOT is not set")
else:
    prismRoot = PRISMROOT

# Get MHExtension plugin root
mhExtensionRoot = MHEXTENSIONROOT

# Add MHExtension to path if needed
if mhExtensionRoot not in sys.path:
    sys.path.insert(0, mhExtensionRoot)

# Ensure PrismCore is available
sys.path.insert(0, os.path.join(prismRoot, "Scripts"))
import PrismCore

from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *

# Get the Blender version to determine the correct region
if bpy.app.version < (2, 80, 0):
    Region = "TOOLS"
else:
    Region = "UI"


def prismInit():
    """Initialize Prism Core"""
    pcore = PrismCore.PrismCore(app="Blender")
    return pcore


# Global storage for active dialogs to prevent garbage collection
_active_dialogs = []


class EntitySelectionDialog(QDialog):
    """Dialog for selecting an entity (asset or shot) using EntityWidget"""

    def __init__(self, core, parent=None):
        super(EntitySelectionDialog, self).__init__(parent)
        self.core = core
        self.selectedData = None
        self.setupUi()

    def setupUi(self):
        self.setWindowTitle("Select Asset or Shot")
        self.resize(800, 600)

        # Main layout
        layout = QVBoxLayout(self)

        # Import and create EntityWidget
        import EntityWidget
        self.w_entities = EntityWidget.EntityWidget(
            core=self.core,
            refresh=True,
            mode="scenefiles",
            pages=["Assets", "Shots"]
        )
        layout.addWidget(self.w_entities)

        # Buttons
        buttonLayout = QHBoxLayout()
        buttonLayout.addStretch()

        self.btn_select = QPushButton("Select")
        self.btn_select.clicked.connect(self.onSelect)
        buttonLayout.addWidget(self.btn_select)

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)
        buttonLayout.addWidget(self.btn_cancel)

        layout.addLayout(buttonLayout)

    def onSelect(self):
        """Get the selected entity data and close the dialog"""
        data = self.w_entities.getCurrentData(returnOne=True)
        if data:
            self.selectedData = data
            self.accept()
        else:
            self.core.popup("Please select an asset or shot", title="No Selection")

    def getSelectedData(self):
        """Return the selected entity data"""
        return self.selectedData


class ModelCreationDialog(QDialog):
    """Dialog for creating a model with asset name, description, and variant number"""

    def __init__(self, core, assetName="", parent=None):
        super(ModelCreationDialog, self).__init__(parent)
        self.core = core
        self.assetName = assetName
        self.resultString = None
        self.setupUi()

    def setupUi(self):
        self.setWindowTitle("Create Model")
        self.resize(250, 500)

        # Set window flags to stay on top but allow interaction with Blender
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)

        # Connect to cleanup when dialog is closed
        self.finished.connect(self.onFinished)

        # Main layout
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Asset Name field
        assetLayout = QHBoxLayout()
        assetLabel = QLabel("Asset Name:")
        assetLabel.setMinimumWidth(120)
        self.e_assetName = QLineEdit()
        self.e_assetName.setText(self.assetName)
        self.e_assetName.textChanged.connect(self.updatePreview)
        assetLayout.addWidget(assetLabel)
        assetLayout.addWidget(self.e_assetName)
        layout.addLayout(assetLayout)

        # Description field
        descLayout = QHBoxLayout()
        descLabel = QLabel("Description:")
        descLabel.setMinimumWidth(120)
        self.e_description = QLineEdit()
        self.e_description.textChanged.connect(self.updatePreview)
        descLayout.addWidget(descLabel)
        descLayout.addWidget(self.e_description)
        layout.addLayout(descLayout)

        # Variant Number field
        variantLayout = QHBoxLayout()
        variantLabel = QLabel("Variant Number:")
        variantLabel.setMinimumWidth(120)
        self.sb_variantNumber = QSpinBox()
        self.sb_variantNumber.setMinimum(0)
        self.sb_variantNumber.setMaximum(9999)
        self.sb_variantNumber.setValue(1)
        self.sb_variantNumber.valueChanged.connect(self.updatePreview)
        variantLayout.addWidget(variantLabel)
        variantLayout.addWidget(self.sb_variantNumber)
        variantLayout.addStretch()
        layout.addLayout(variantLayout)

        # Objects GroupBox
        self.gb_objects = QGroupBox("Objects (Meshes and Curves)")
        objectsLayout = QVBoxLayout(self.gb_objects)

        # List widget for objects
        self.lw_objects = QListWidget()
        self.lw_objects.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.lw_objects.setContextMenuPolicy(Qt.CustomContextMenu)
        self.lw_objects.customContextMenuRequested.connect(self.rcObjects)
        objectsLayout.addWidget(self.lw_objects)

        # Add button
        self.b_addObjects = QPushButton("Add Selected")
        self.b_addObjects.setFocusPolicy(Qt.NoFocus)
        self.b_addObjects.clicked.connect(self.addObjects)
        objectsLayout.addWidget(self.b_addObjects)

        layout.addWidget(self.gb_objects)

        # Add separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator)

        # Preview label
        previewLayout = QVBoxLayout()
        previewTitleLabel = QLabel("Preview:")
        previewTitleLabel.setStyleSheet("font-weight: bold;")
        self.l_preview = QLabel("")
        self.l_preview.setStyleSheet("font-size: 12pt; padding: 10px; background-color: #2a2a2a; border: 1px solid #555;")
        self.l_preview.setWordWrap(True)
        previewLayout.addWidget(previewTitleLabel)
        previewLayout.addWidget(self.l_preview)
        layout.addLayout(previewLayout)

        # Update initial preview
        self.updatePreview()

        # Initialize object list
        self.objects = []

        # Buttons
        layout.addStretch()
        buttonLayout = QHBoxLayout()
        buttonLayout.addStretch()

        self.btn_ok = QPushButton("OK")
        self.btn_ok.clicked.connect(self.onOk)
        buttonLayout.addWidget(self.btn_ok)

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)
        buttonLayout.addWidget(self.btn_cancel)

        layout.addLayout(buttonLayout)

        # Auto-populate with currently selected objects
        self.addObjects()

    def updatePreview(self):
        """Update the preview label based on current field values"""
        assetName = self.e_assetName.text().strip()
        description = self.e_description.text().strip()
        variantNumber = self.sb_variantNumber.value()

        # Build the preview string
        parts = []
        if assetName:
            parts.append(assetName)
        if description:
            parts.append(description)
        if variantNumber > 0:
            # Format variant number with "var" prefix and 3-digit zero padding
            parts.append(f"var{variantNumber:03d}")

        if parts:
            previewText = "_".join(parts) + "_<modelName>"
        else:
            previewText = "<modelName>"

        self.l_preview.setText(previewText)

    def onOk(self):
        """Validate and create the model"""
        assetName = self.e_assetName.text().strip()
        description = self.e_description.text().strip()
        variantNumber = self.sb_variantNumber.value()

        # Build the result string (without <modelName>)
        parts = []
        if assetName:
            parts.append(assetName)
        if description:
            parts.append(description)
        if variantNumber > 0:
            # Format variant number with "var" prefix and 3-digit zero padding
            parts.append(f"var{variantNumber:03d}")

        if parts:
            self.resultString = "_".join(parts)
            selectedObjects = self.getObjects()

            print(f"Model creation string: {self.resultString}")
            print(f"Selected objects: {[obj.name for obj in selectedObjects]}")

            msg = f"Model will be created with prefix:\n\n{self.resultString}"
            if selectedObjects:
                msg += f"\n\nSelected objects ({len(selectedObjects)}):\n"
                msg += "\n".join([f"  - {obj.name}" for obj in selectedObjects[:10]])
                if len(selectedObjects) > 10:
                    msg += f"\n  ... and {len(selectedObjects) - 10} more"

            self.core.popup(msg, title="MH Create Model - Success")
            self.close()
        else:
            self.core.popup("Please fill in at least the Asset Name field", title="Validation Error")

    def getResultString(self):
        """Return the result string (without <modelName>)"""
        return self.resultString

    def addObjects(self):
        """Add selected meshes and curves from the scene"""
        # Get selected objects from Blender using view_layer
        try:
            selectedObjects = list(bpy.context.view_layer.objects.selected)
        except AttributeError:
            # Fallback to checking all objects for selection
            selectedObjects = [obj for obj in bpy.data.objects if obj.select_get()]

        print(f"DEBUG: Total selected objects: {len(selectedObjects)}")
        print(f"DEBUG: Selected object names: {[obj.name for obj in selectedObjects]}")

        # Filter for only MESH and CURVE types
        validObjects = [obj for obj in selectedObjects if obj.type in ['MESH', 'CURVE']]

        print(f"DEBUG: Valid objects (MESH/CURVE): {len(validObjects)}")
        print(f"DEBUG: Valid object names: {[obj.name for obj in validObjects]}")

        if not validObjects:
            self.core.popup("Please select at least one mesh or curve object", title="No Valid Objects")
            return

        # Add objects to the list (avoid duplicates)
        addedCount = 0
        for obj in validObjects:
            if obj not in self.objects:
                self.objects.append(obj)
                self.lw_objects.addItem(obj.name)
                addedCount += 1
                print(f"DEBUG: Added {obj.name} to list")
            else:
                print(f"DEBUG: {obj.name} already in list, skipping")

        print(f"DEBUG: Added {addedCount} objects. Total objects in list: {len(self.objects)}")
        print(f"DEBUG: List widget item count: {self.lw_objects.count()}")

    def rcObjects(self, pos):
        """Right-click context menu for object list"""
        item = self.lw_objects.itemAt(pos)

        if item is None:
            self.lw_objects.setCurrentRow(-1)

        createMenu = QMenu()

        if item is not None:
            actRemove = QAction("Remove", self)
            actRemove.triggered.connect(lambda: self.removeItem(item))
            createMenu.addAction(actRemove)

        actClear = QAction("Clear", self)
        actClear.triggered.connect(self.clearItems)
        createMenu.addAction(actClear)

        createMenu.exec_(self.lw_objects.mapToGlobal(pos))

    def removeItem(self, item):
        """Remove selected items from the list"""
        items = self.lw_objects.selectedItems()
        for item in reversed(items):
            rowNum = self.lw_objects.row(item)
            del self.objects[rowNum]
            self.lw_objects.takeItem(rowNum)

    def clearItems(self):
        """Clear all objects from the list"""
        self.lw_objects.clear()
        self.objects = []

    def getObjects(self):
        """Return the list of selected objects"""
        return self.objects

    def onFinished(self):
        """Cleanup when dialog is closed"""
        global _active_dialogs
        if self in _active_dialogs:
            _active_dialogs.remove(self)


class MH_CreateModel(bpy.types.Operator):
    """Create Model using MH pipeline"""
    bl_idname = "object.mh_create_model"
    bl_label = "Create Model"

    def execute(self, context):
        global _active_dialogs

        try:
            # Get the current scene filename
            fileName = pcore.getCurrentFileName()

            # Check if file is in the pipeline
            fileInPipeline = fileName and pcore.fileInPipeline(fileName)

            if not fileInPipeline:
                # File is not in pipeline or no file opened - use EntitySelectionDialog
                print("File is not in pipeline or no file opened. Opening Entity Selection Dialog...")

                # Open EntitySelectionDialog to select an asset or shot
                dialog = EntitySelectionDialog(core=pcore)
                pcore.parentWindow(dialog)
                result = dialog.exec_()

                assetName = ""  # Default to empty

                if result == QDialog.Accepted:
                    # Get the selected entity data
                    entityData = dialog.getSelectedData()

                    if entityData:
                        print(f"Selected entity data: {entityData}")

                        # Get entity type
                        entityType = entityData.get("type")

                        if entityType == "asset":
                            assetName = os.path.basename(entityData.get("asset_path", ""))
                            assetPath = entityData.get("asset_path", "")

                            print(f"Asset Name: {assetName}")
                            print(f"Asset Path: {assetPath}")
                            print(f"Full entity data: {entityData}")

                        elif entityType == "shot":
                            shotName = entityData.get("shot", "Unknown")
                            sequenceName = entityData.get("sequence", "")
                            episodeName = entityData.get("episode", "")

                            print(f"Shot Name: {shotName}")
                            if sequenceName:
                                print(f"Sequence: {sequenceName}")
                            if episodeName:
                                print(f"Episode: {episodeName}")

                            msg = f"This is a shot, not an asset.\n\nShot: {shotName}"
                            if sequenceName:
                                msg += f"\nSequence: {sequenceName}"
                            if episodeName:
                                msg += f"\nEpisode: {episodeName}"

                            pcore.popup(msg, title="MH Create Model")
                            return {"CANCELLED"}
                        else:
                            print(f"Unknown entity type: {entityType}")
                            pcore.popup(f"Unknown entity type: {entityType}", title="MH Create Model")
                            return {"CANCELLED"}
                else:
                    print("Entity selection cancelled - proceeding with empty asset name")

                # Open ModelCreationDialog with the asset name (empty if cancelled)
                modelDialog = ModelCreationDialog(core=pcore, assetName=assetName)
                pcore.parentWindow(modelDialog)

                # Keep reference to prevent garbage collection
                _active_dialogs.append(modelDialog)

                modelDialog.show()  # Use show() instead of exec_() to allow Blender interaction

            else:
                # File is in the pipeline - extract from scene file
                print(f"File is in pipeline: {fileName}")

                # Get scene file data with entity extraction from path
                fnameData = pcore.getScenefileData(fileName, getEntityFromPath=True)

                if not fnameData:
                    print("Could not get scene file data")
                    pcore.popup("Could not extract data from the scene file", title="MH Create Model")
                    return {"CANCELLED"}

                # Get entity type
                entityType = fnameData.get("type") or fnameData.get("entityType")

                if entityType == "asset":
                    # Get asset name from the path data
                    assetName = fnameData.get("asset", "Unknown")
                    assetPath = fnameData.get("asset_path", "")

                    print(f"Asset Name: {assetName}")
                    print(f"Asset Path: {assetPath}")

                    # Show all available data for debugging
                    print(f"Full scene data: {fnameData}")

                    # Extract additional useful info using extractKeysFromPath
                    template = pcore.projects.getTemplatePath("assetScenefiles")
                    pathData = pcore.projects.extractKeysFromPath(fileName, template, context=fnameData)

                    print(f"Extracted path data: {pathData}")

                    # Open ModelCreationDialog with the asset name
                    modelDialog = ModelCreationDialog(core=pcore, assetName=assetName)
                    pcore.parentWindow(modelDialog)

                    # Keep reference to prevent garbage collection
                    _active_dialogs.append(modelDialog)

                    modelDialog.show()  # Use show() instead of exec_() to allow Blender interaction

                elif entityType == "shot":
                    shotName = fnameData.get("shot", "Unknown")
                    sequenceName = fnameData.get("sequence", "")
                    episodeName = fnameData.get("episode", "")

                    print(f"Shot Name: {shotName}")
                    if sequenceName:
                        print(f"Sequence: {sequenceName}")
                    if episodeName:
                        print(f"Episode: {episodeName}")

                    msg = f"This is a shot, not an asset.\n\nShot: {shotName}"
                    if sequenceName:
                        msg += f"\nSequence: {sequenceName}"
                    if episodeName:
                        msg += f"\nEpisode: {episodeName}"

                    pcore.popup(msg, title="MH Create Model")

                else:
                    print(f"Unknown entity type: {entityType}")
                    pcore.popup(f"Unknown entity type: {entityType}", title="MH Create Model")

        except Exception as e:
            import traceback
            print(f"Error in MH_CreateModel: {str(e)}")
            print(traceback.format_exc())
            pcore.popup(f"Error: {str(e)}", title="MH Create Model Error")
            return {"CANCELLED"}

        return {"FINISHED"}


class MH_OpsPanel(bpy.types.Panel):
    """MH Operations Panel"""
    bl_label = "MH Ops"
    bl_idname = "MH_PT_ops_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = Region
    bl_category = "Prism"

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.operator("object.mh_create_model")


# Registration functions
def register():
    """Register Blender classes"""
    if bpy.app.background:
        return

    try:
        # Initialize QApplication if needed
        qapp = QApplication.instance()
        if qapp is None:
            qapp = QApplication(sys.argv)

        # Initialize Prism Core as a global variable
        global pcore
        pcore = prismInit()

        bpy.utils.register_class(MH_CreateModel)
        bpy.utils.register_class(MH_OpsPanel)
        print("MH Blender Extension registered successfully")
    except Exception as e:
        print(f"ERROR - MHBlenderInit registration - {str(e)}")


def unregister():
    """Unregister Blender classes"""
    if bpy.app.background:
        return

    try:
        bpy.utils.unregister_class(MH_CreateModel)
        bpy.utils.unregister_class(MH_OpsPanel)
        print("MH Blender Extension unregistered")
    except Exception as e:
        print(f"ERROR - MHBlenderInit unregistration - {str(e)}")


# Auto-register when loaded as startup script
if __name__ != "__main__":
    register()
