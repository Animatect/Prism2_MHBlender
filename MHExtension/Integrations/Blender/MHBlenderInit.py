# -*- coding: utf-8 -*-
#
# MH Blender Extension Integration
# Adds custom MH_Ops panel to Blender's Prism panel category
#

import os
import sys


import bpy
from mathutils import Matrix

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

from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *
from qtpy.QtWidgets import QListWidgetItem

# Get the Blender version to determine the correct region
if bpy.app.version < (2, 80, 0):
    Region = "TOOLS"
else:
    Region = "UI"


# Global pcore - will be set by PrismInit.py or initialized standalone
pcore = None


def initWithCore(prism_core):
    """Initialize MH Extension with an existing Prism Core instance from PrismInit.py"""
    global pcore
    pcore = prism_core

    # Register Blender classes
    _register_classes()

    print("MH Blender Extension initialized with shared Prism Core")
    return pcore


def _register_classes():
    """Register Blender operator and panel classes"""
    try:
        bpy.utils.register_class(MH_CreateModel)
        bpy.utils.register_class(MH_RenamePlant)
        bpy.utils.register_class(MH_OpsPanel)
        print("MH Blender Extension classes registered successfully")
    except Exception as e:
        print(f"ERROR - MHBlenderInit class registration - {str(e)}")


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
        self.e_assetName.setToolTip("El nombre de un asset existente en el proyecto o uno a ser creado.")
        self.e_assetName.textChanged.connect(self.updatePreview)
        assetLayout.addWidget(assetLabel)
        assetLayout.addWidget(self.e_assetName)
        layout.addLayout(assetLayout)

        # Description field
        descLayout = QHBoxLayout()
        descLabel = QLabel("Description:")
        descLabel.setMinimumWidth(120)
        self.e_description = QLineEdit()
        self.e_description.setText("Main")  # Set default value
        self.e_description.setToolTip("Un adjetivo que describa lo que hace a ésta variante distinta de las demás, por ejemplo, 'Alta', 'Amarilla', 'Dañada', etc.")
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
        self.sb_variantNumber.setToolTip("Dentro de variantes con la misma descripción éste número sirve como un identificador.")
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

        # Add separator
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.HLine)
        separator2.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator2)

        # Checkboxes for options
        optionsLayout = QVBoxLayout()

        self.chb_resetTransforms = QCheckBox("Reset Transforms (Apply/Freeze)")
        self.chb_resetTransforms.setChecked(True)
        self.chb_resetTransforms.setToolTip("Aplica/congela las transformaciones de los objetos (ubicación, rotación, escala)")
        optionsLayout.addWidget(self.chb_resetTransforms)

        self.chb_createExportState = QCheckBox("Create Export State")
        self.chb_createExportState.setChecked(True)
        self.chb_createExportState.setToolTip("Crea un estado de exportación en el State Manager de Prism")
        optionsLayout.addWidget(self.chb_createExportState)

        layout.addLayout(optionsLayout)

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

    def selectObjectsAndApplyTransforms(self, objects):

        for obj in objects:
            self.freeze_transforms(obj)
            print(f"Applied transforms to {len(objects)} object(s)")

    def freeze_transforms(self, obj):
        mw = obj.matrix_world.copy()

        # 1. Apply matrix to mesh data
        if obj.type == 'MESH':
            obj.data.transform(mw)
            obj.data.update()

        # 2. Reset object matrix
        obj.matrix_world = Matrix.Identity(4)

    def reset_transforms(self, obj): # de vuelta a ident
        # Bake matrix_world into transforms
        mw = obj.matrix_world.copy()

        # Decompose new transforms
        obj.location = mw.to_translation()
        obj.rotation_euler = mw.to_euler()
        obj.scale = mw.to_scale()

        # Reset world matrix
        obj.matrix_world = Matrix.Identity(4)

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

        if not parts:
            self.core.popup("Please fill in at least the Asset Name field", title="Validation Error")
            return

        self.resultString = "_".join(parts)
        selectedObjects = self.getObjects()

        if not selectedObjects:
            self.core.popup("Please add at least one object to the selection", title="Validation Error")
            return

        # Auto-increment variant number if name already exists
        originalVariantNumber = variantNumber
        while bpy.data.objects.get(self.resultString) is not None:
            variantNumber += 1
            parts = []
            if assetName:
                parts.append(assetName)
            if description:
                parts.append(description)
            if variantNumber > 0:
                parts.append(f"var{variantNumber:03d}")
            self.resultString = "_".join(parts)
            print(f"Name conflict detected. Incremented variant to: {variantNumber}")

        if variantNumber != originalVariantNumber:
            print(f"Variant number auto-incremented from {originalVariantNumber} to {variantNumber}")

        print(f"Model creation string: {self.resultString}")
        print(f"Selected objects: {[obj.name for obj in selectedObjects]}")

        # Process each object
        try:
            # Step 1: Create or get the export collection
            collectionName = f"ASSET_{assetName}_EXPORT"
            exportCollection = bpy.data.collections.get(collectionName)

            if not exportCollection:
                # Create the collection
                exportCollection = bpy.data.collections.new(collectionName)
                bpy.context.scene.collection.children.link(exportCollection)
                print(f"Created collection: {collectionName}")
            else:
                print(f"Using existing collection: {collectionName}")

            # Step 2: Check if asset null already exists, create if not
            assetNullName = assetName
            assetNull = bpy.data.objects.get(assetNullName)

            if not assetNull:
                # Create asset null (empty object)
                assetNull = bpy.data.objects.new(assetNullName, None)
                exportCollection.objects.link(assetNull)
                print(f"Created asset null: {assetNullName}")
            else:
                print(f"Using existing asset null: {assetNullName}")
                # Move to export collection if not already there
                if assetNull.name not in exportCollection.objects:
                    exportCollection.objects.link(assetNull)
                    # Remove from other collections
                    for col in assetNull.users_collection:
                        if col != exportCollection:
                            col.objects.unlink(assetNull)

            # Step 3: Create model group null (prefix without <modelName>)
            modelGroupName = self.resultString
            modelGroupNull = bpy.data.objects.new(modelGroupName, None)
            exportCollection.objects.link(modelGroupNull)
            print(f"Created model group null: {modelGroupName}")

            # Step 4: Parent model group to asset null
            modelGroupNull.parent = assetNull

            # Step 5: Process each selected object
            for obj in selectedObjects:
                # Get the original object name to use as modelName
                originalName = obj.name

                # Build the new object name: prefix_modelName
                newObjectName = f"{self.resultString}_{originalName}"

                # Rename the object
                obj.name = newObjectName
                print(f"Renamed object: {originalName} -> {newObjectName}")

                # Rename the mesh/curve data with appropriate suffix
                if obj.type == 'MESH' and obj.data:
                    obj.data.name = f"{newObjectName}_Mesh"
                    print(f"Renamed mesh data to: {obj.data.name}")
                elif obj.type == 'CURVE' and obj.data:
                    obj.data.name = f"{newObjectName}_Curve"
                    print(f"Renamed curve data to: {obj.data.name}")

                # Parent the object to the model group null
                obj.parent = modelGroupNull
                print(f"Parented {newObjectName} to {modelGroupName}")

                # Move object to export collection if not already there
                if obj.name not in exportCollection.objects:
                    exportCollection.objects.link(obj)
                    # Remove from other collections
                    for col in obj.users_collection:
                        if col != exportCollection:
                            col.objects.unlink(obj)
                    print(f"Moved {newObjectName} to collection {collectionName}")

            # Step 6: Reset transforms if requested
            if self.chb_resetTransforms.isChecked():
                objs = selectedObjects
                self.selectObjectsAndApplyTransforms(objs)

                # Deselect all
                bpy.ops.object.select_all(action='DESELECT')

            # Step 7: Create export state if requested
            if self.chb_createExportState.isChecked():
                print("Creating export state...")
                try:
                    # Check if State Manager is available
                    if hasattr(self.core, 'stateManager') and self.core.stateManager:
                        sm = self.core.stateManager()
                        if sm:
                            # Create export state
                            stateItem = sm.createState("Export", setActive=True)
                            if stateItem and hasattr(stateItem, 'ui'):
                                exportState = stateItem.ui
                                # Set the state name to "Modeling"
                                if hasattr(exportState, 'e_name'):
                                    exportState.e_name.setText("Modeling")

                                # Add the ASSET_<AssetName>_EXPORT collection to the export state
                                assetExportCollection = bpy.data.collections.get(f"ASSET_{assetName}_EXPORT")
                                if assetExportCollection:
                                    # Directly add only the collection to nodes (not its contents)
                                    collectionNode = self.core.appPlugin.getNode(assetExportCollection)
                                    exportState.nodes = [collectionNode]

                                    # Manually update the UI list widget (bypass updateObjectList which calls sm_export_updateObjects)
                                    exportState.lw_objects.clear()
                                    for node in exportState.nodes:
                                        if self.core.appPlugin.isNodeValid(exportState, node):
                                            item = QListWidgetItem(self.core.appPlugin.getNodeName(exportState, node))
                                            exportState.lw_objects.addItem(item)

                                    sm.saveStatesToScene()

                                print(f"Created export state: Modeling with collection {collectionName}")
                                msg_exportState = "\nExport state created successfully!"
                            else:
                                print("Failed to create export state")
                                msg_exportState = "\nFailed to create export state"
                        else:
                            print("State Manager not available")
                            msg_exportState = "\nState Manager not available"
                    else:
                        print("State Manager not available")
                        msg_exportState = "\nState Manager not available"
                except Exception as e:
                    print(f"Error creating export state: {e}")
                    msg_exportState = f"\nError creating export state: {e}"
            else:
                msg_exportState = ""

            msg = f"Model created successfully!\n\n"
            msg += f"Collection: {collectionName}\n"
            msg += f"Asset Null: {assetNullName}\n"
            msg += f"Model Group: {modelGroupName}\n"
            if self.chb_resetTransforms.isChecked():
                msg += "\nTransforms applied/frozen"
            msg += msg_exportState
            msg += f"\n\nProcessed {len(selectedObjects)} object(s):\n"
            msg += "\n".join([f"  - {obj.name}" for obj in selectedObjects[:10]])
            if len(selectedObjects) > 10:
                msg += f"\n  ... and {len(selectedObjects) - 10} more"

            self.core.popup(msg, title="MH Create Model - Success", severity="info")
            self.close()

        except Exception as e:
            import traceback
            error_msg = f"Error creating model:\n\n{str(e)}\n\n{traceback.format_exc()}"
            print(error_msg)
            self.core.popup(error_msg, title="MH Create Model - Error")

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

                            pcore.popup(msg, title="MH Create Model", severity="info")
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

                    #print(f"Asset Name: {assetName}")
                    #print(f"Asset Path: {assetPath}")

                    # Show all available data for debugging
                    #print(f"Full scene data: {fnameData}")

                    # Extract additional useful info using extractKeysFromPath
                    template = pcore.projects.getTemplatePath("assetScenefiles")
                    pathData = pcore.projects.extractKeysFromPath(fileName, template, context=fnameData)

                    #print(f"Extracted path data: {pathData}")

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

                    pcore.popup(msg, title="MH Create Model", severity="info")

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


class MH_RenamePlant(bpy.types.Operator):
    """Rename Plant using MH pipeline"""
    bl_idname = "object.mh_rename_plant"
    bl_label = "Rename Plant"

    def execute(self, context):
        try:
            # TODO: Implement rename plant functionality
            pcore.popup("Rename Plant functionality coming soon!", title="MH Rename Plant")
        except Exception as e:
            print(f"ERROR - MH_RenamePlant - {str(e)}")

        return {'FINISHED'}


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
        row = layout.row()
        row.operator("object.mh_rename_plant")


# Registration functions
def register():
    """Register Blender classes - standalone mode (creates its own PrismCore)

    Note: When integrated with PrismInit.py, use initWithCore() instead.
    This function is kept for backwards compatibility when MHBlenderInit.py
    is loaded as a standalone startup script.
    """
    if bpy.app.background:
        return

    try:
        # Initialize QApplication if needed
        qapp = QApplication.instance()
        if qapp is None:
            qapp = QApplication(sys.argv)

        # Initialize Prism Core as a global variable (standalone mode)
        global pcore
        import PrismCore
        pcore = PrismCore.PrismCore(app="Blender", prismArgs=["noProjectBrowser"])

        _register_classes()
        print("MH Blender Extension registered successfully (standalone mode)")
    except Exception as e:
        print(f"ERROR - MHBlenderInit registration - {str(e)}")


def unregister():
    """Unregister Blender classes"""
    if bpy.app.background:
        return

    try:
        bpy.utils.unregister_class(MH_CreateModel)
        bpy.utils.unregister_class(MH_RenamePlant)
        bpy.utils.unregister_class(MH_OpsPanel)
        print("MH Blender Extension unregistered")
    except Exception as e:
        print(f"ERROR - MHBlenderInit unregistration - {str(e)}")


# Auto-register when loaded as startup script
if __name__ != "__main__":
    register()
