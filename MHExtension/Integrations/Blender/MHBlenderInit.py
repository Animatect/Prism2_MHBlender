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
from qtpy.QtWidgets import QListWidgetItem, QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QSpinBox, QRadioButton, QGroupBox, QSplitter, QLineEdit

# Get the Blender version to determine the correct region
if bpy.app.version < (2, 80, 0):
    Region = "TOOLS"
else:
    Region = "UI"


# Global pcore - will be set by PrismInit.py or initialized standalone
pcore = None


def createExportStateStandalone(core, assetName, collectionName):
    """Standalone function to create export state (called from timer)"""
    print("Creating/updating export state (standalone)...")
    try:
        # Check if State Manager is available
        if hasattr(core, 'stateManager') and core.stateManager:
            sm = core.stateManager()
            if sm:
                # Check if a state named "Modeling" already exists
                existingState = None
                stateItem = None
                for i in range(sm.tw_export.topLevelItemCount()):
                    item = sm.tw_export.topLevelItem(i)
                    if hasattr(item, 'ui') and hasattr(item.ui, 'e_name'):
                        if item.ui.e_name.text() == "Modeling":
                            existingState = item
                            break

                if existingState:
                    # Use existing state
                    stateItem = existingState
                    print("Found existing 'Modeling' export state, updating it...")
                    stateAction = "updated"
                else:
                    # Create new export state
                    stateItem = sm.createState("Export", setActive=True)
                    stateAction = "created"
                    if stateItem and hasattr(stateItem, 'ui'):
                        # Set the state name to "Modeling"
                        if hasattr(stateItem.ui, 'e_name'):
                            stateItem.ui.e_name.setText("Modeling")

                if stateItem and hasattr(stateItem, 'ui'):
                    exportState = stateItem.ui

                    # Add the ASSET_<AssetName>_EXPORT collection to the export state
                    assetExportCollection = bpy.data.collections.get(f"ASSET_{assetName}_EXPORT")
                    if assetExportCollection:
                        # Use Prism's built-in method to properly add the collection
                        # This links the collection to the task's tracking collection
                        core.appPlugin.sm_export_addObjects(
                            exportState,
                            objects=[assetExportCollection]
                        )

                        # Update the UI to reflect the changes
                        exportState.updateUi()
                        sm.saveStatesToScene()

                    print(f"{stateAction.capitalize()} export state: Modeling with collection {collectionName}")
                else:
                    print("Failed to create export state")
            else:
                print("State Manager not available")
        else:
            print("State Manager not available")
    except Exception as e:
        import traceback
        print(f"Error creating export state: {e}\n{traceback.format_exc()}")


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

        # Preset categories and tags dictionary
        self.presetCategories = {
            "None": [],
            "plantParts": [
                "frutos",
                "flores",
                "hojas",
                "lianas",
                "tallo",
                "tronco",
                "raices"
            ]
        }

        self.setupUi()

    def setupUi(self):
        self.setWindowTitle("Create Model")
        self.resize(500, 500)

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

        # Presets dropdown
        presetLayout = QHBoxLayout()
        presetLabel = QLabel("Preset Category:")
        presetLabel.setMinimumWidth(120)
        self.cb_presetCategory = QComboBox()
        self.cb_presetCategory.addItems(list(self.presetCategories.keys()))
        self.cb_presetCategory.setToolTip("Selecciona una categoría de presets para asignar tags a los objetos")
        self.cb_presetCategory.currentTextChanged.connect(self.onPresetCategoryChanged)
        presetLayout.addWidget(presetLabel)
        presetLayout.addWidget(self.cb_presetCategory)
        layout.addLayout(presetLayout)

        # Create a splitter for resizable sections
        self.splitter = QSplitter(Qt.Vertical)
        layout.addWidget(self.splitter)

        # Objects GroupBox (resizable via splitter)
        self.gb_objects = QGroupBox("Objects (Meshes and Curves)")
        objectsLayout = QVBoxLayout(self.gb_objects)

        # Table widget for objects with description, variant and tag columns
        self.tw_objects = QTableWidget()
        self.tw_objects.setColumnCount(4)
        self.tw_objects.setHorizontalHeaderLabels(["Object Name", "Description", "Variant", "Tag"])
        self.tw_objects.horizontalHeader().setStretchLastSection(False)
        self.tw_objects.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tw_objects.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tw_objects.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.tw_objects.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.tw_objects.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tw_objects.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.tw_objects.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tw_objects.customContextMenuRequested.connect(self.rcObjects)
        self.tw_objects.setMinimumHeight(150)  # Minimum height
        objectsLayout.addWidget(self.tw_objects)

        # Add button
        self.b_addObjects = QPushButton("Add Selected")
        self.b_addObjects.setFocusPolicy(Qt.NoFocus)
        self.b_addObjects.clicked.connect(self.addObjects)
        objectsLayout.addWidget(self.b_addObjects)

        self.splitter.addWidget(self.gb_objects)

        # Preview GroupBox (always visible)
        self.gb_preview = QGroupBox("Preview")
        previewLayout = QVBoxLayout(self.gb_preview)

        self.l_preview = QLabel("")
        self.l_preview.setStyleSheet("font-size: 10pt; padding: 10px; background-color: #2a2a2a; border: 1px solid #555;")
        self.l_preview.setWordWrap(True)
        self.l_preview.setMinimumHeight(80)
        previewLayout.addWidget(self.l_preview)

        self.splitter.addWidget(self.gb_preview)

        # Set initial splitter sizes (objects gets more space)
        self.splitter.setSizes([300, 150])
        self.splitter.setStretchFactor(0, 1)  # Objects section stretches more

        # Update initial preview
        self.updatePreview()

        # Initialize object list
        self.objects = []

        # Options layout
        optionsLayout = QVBoxLayout()

        # Transform options group box
        transformGroupBox = QGroupBox("Transform Options")
        transformLayout = QVBoxLayout(transformGroupBox)

        self.rb_zeroTransforms = QRadioButton("Zero Transforms")
        self.rb_zeroTransforms.setChecked(True)  # Default
        self.rb_zeroTransforms.setToolTip("Resetea las transformaciones a cero (ubicación, rotación, escala a valores por defecto)")
        transformLayout.addWidget(self.rb_zeroTransforms)

        self.rb_freezeTransforms = QRadioButton("Freeze Transforms")
        self.rb_freezeTransforms.setToolTip("Aplica/congela las transformaciones en la geometría del objeto")
        transformLayout.addWidget(self.rb_freezeTransforms)

        self.rb_doNothing = QRadioButton("Do Nothing")
        self.rb_doNothing.setToolTip("No modifica las transformaciones de los objetos")
        transformLayout.addWidget(self.rb_doNothing)

        optionsLayout.addWidget(transformGroupBox)

        # Export state checkbox
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

        # Show format explanation
        previewText = "Format: AssetName_Description_var###_<modelName or tag>\n"
        previewText += "\nNote: Each object has its own description and variant number"

        # Show examples from actual objects in the table if any exist
        if self.tw_objects.rowCount() > 0:
            previewText += "\n\nExamples from current objects:"

            # Get first 3 objects as examples
            for row in range(min(3, self.tw_objects.rowCount())):
                # Get object name
                nameItem = self.tw_objects.item(row, 0)
                if nameItem:
                    objName = nameItem.text()

                    # Get description from column 1
                    descLineEdit = self.tw_objects.cellWidget(row, 1)
                    objDescription = descLineEdit.text().strip() if descLineEdit else ""

                    # Get variant from column 2
                    variantSpinBox = self.tw_objects.cellWidget(row, 2)
                    variantNum = variantSpinBox.value() if variantSpinBox else 1

                    # Get tag from column 3
                    tagCombo = self.tw_objects.cellWidget(row, 3)
                    tag = tagCombo.currentText() if tagCombo else ""

                    # Build example name
                    parts = []
                    if assetName:
                        parts.append(assetName)
                    if objDescription:
                        parts.append(objDescription)
                    if variantNum > 0:
                        parts.append(f"var{variantNum:03d}")

                    # Use tag or object name
                    modelName = tag if tag else objName
                    parts.append(modelName)

                    exampleName = "_".join(parts) if parts else modelName
                    previewText += f"\n  • {exampleName}"

        self.l_preview.setText(previewText)

    def onPresetCategoryChanged(self, category):
        """Handle preset category change - update tag dropdowns in all rows"""
        tags = self.presetCategories.get(category, [])

        # Update all existing rows with new tag options
        for row in range(self.tw_objects.rowCount()):
            tagCombo = self.tw_objects.cellWidget(row, 3)  # Tag is now column 3
            if tagCombo:
                # Store current selection if it exists in new tags
                currentTag = tagCombo.currentText()
                tagCombo.clear()

                if category != "None" and tags:
                    tagCombo.addItem("")  # Add empty option
                    tagCombo.addItems(tags)

                    # Restore previous selection if still valid
                    if currentTag in tags:
                        tagCombo.setCurrentText(currentTag)
                else:
                    tagCombo.addItem("")  # Only empty option when None selected

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

        # Validate asset name
        if not assetName:
            self.core.popup("Please fill in at least the Asset Name field", title="Validation Error")
            return

        selectedObjects = self.getObjects()

        if not selectedObjects:
            self.core.popup("Please add at least one object to the selection", title="Validation Error")
            return

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

            # Step 3: Create variant group nulls for each unique variant+description combination
            # Get object tags, variants, and descriptions
            objectTags = self.getObjectTags()
            objectVariants = self.getObjectVariants()
            objectDescriptions = self.getObjectDescriptions()

            # Find all unique (variant, description) combinations and create variant group nulls
            uniqueVariantDescriptions = set()
            for idx in range(len(selectedObjects)):
                variantNum = objectVariants.get(idx, 1)
                desc = objectDescriptions.get(idx, "")
                uniqueVariantDescriptions.add((variantNum, desc))

            variantGroupNulls = {}  # Maps (variant, description) tuple to variant group null

            for variantNumber, description in uniqueVariantDescriptions:
                # Build variant group name: AssetName_Description_var###
                parts = []
                if assetName:
                    parts.append(assetName)
                if description:
                    parts.append(description)
                if variantNumber > 0:
                    parts.append(f"var{variantNumber:03d}")

                variantGroupName = "_".join(parts) if parts else f"var{variantNumber:03d}"

                # Create variant group null
                variantGroupNull = bpy.data.objects.new(variantGroupName, None)
                exportCollection.objects.link(variantGroupNull)
                print(f"Created variant group null: {variantGroupName}")

                # Parent variant group to asset null
                variantGroupNull.parent = assetNull

                # Store reference
                variantGroupNulls[(variantNumber, description)] = variantGroupNull

            # Step 4: Process each selected object
            usedTagNames = {}  # Track how many times each tag has been used

            for idx, obj in enumerate(selectedObjects):
                # Get the original object name to use as modelName
                originalName = obj.name

                # Get the variant number and description for this object
                variantNumber = objectVariants.get(idx, 1)
                objDescription = objectDescriptions.get(idx, "")

                # Get the variant group null for this variant+description combination
                variantGroupNull = variantGroupNulls[(variantNumber, objDescription)]

                # Build the prefix for this object: AssetName_Description_var###
                parts = []
                if assetName:
                    parts.append(assetName)
                if objDescription:
                    parts.append(objDescription)
                if variantNumber > 0:
                    parts.append(f"var{variantNumber:03d}")

                objectPrefix = "_".join(parts) if parts else ""

                # Check if this object has a tag assigned
                if idx in objectTags:
                    tag = objectTags[idx]

                    # Build key for tracking this tag with this variant
                    tagKey = f"{objectPrefix}_{tag}"

                    # Handle version numbering for duplicate tags within same variant
                    if tagKey in usedTagNames:
                        usedTagNames[tagKey] += 1
                        modelName = f"{tag}.v{usedTagNames[tagKey]:02d}"
                    else:
                        # Check if base tag name already exists
                        baseName = f"{objectPrefix}_{tag}"
                        if bpy.data.objects.get(baseName) is not None:
                            usedTagNames[tagKey] = 2
                            modelName = f"{tag}.v02"
                        else:
                            usedTagNames[tagKey] = 1
                            modelName = tag
                else:
                    # No tag selected, use original object name
                    modelName = originalName

                # Build the new object name: prefix_modelName
                newObjectName = f"{objectPrefix}_{modelName}" if objectPrefix else modelName

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

                # Parent the object to the variant group null
                obj.parent = variantGroupNull
                print(f"Parented {newObjectName} to {variantGroupNull.name}")

                # Move object to export collection if not already there
                if obj.name not in exportCollection.objects:
                    exportCollection.objects.link(obj)
                    # Remove from other collections
                    for col in obj.users_collection:
                        if col != exportCollection:
                            col.objects.unlink(obj)
                    print(f"Moved {newObjectName} to collection {collectionName}")

            # Step 6: Apply transforms based on selected option
            if self.rb_zeroTransforms.isChecked():
                print("Applying zero transforms...")
                for obj in selectedObjects:
                    self.reset_transforms(obj)
                print(f"Applied zero transforms to {len(selectedObjects)} object(s)")
            elif self.rb_freezeTransforms.isChecked():
                print("Applying freeze transforms...")
                for obj in selectedObjects:
                    self.freeze_transforms(obj)
                print(f"Applied freeze transforms to {len(selectedObjects)} object(s)")
            else:
                print("Skipping transform operations (Do Nothing selected)")

            # Step 7: Deselect all objects before creating export state
            bpy.ops.object.select_all(action='DESELECT')

            # Force Blender to update the view layer and depsgraph
            bpy.context.view_layer.update()
            bpy.context.evaluated_depsgraph_get().update()

            print("Deselected all objects and refreshed view layer")

            # Step 8: Build success message
            msg = f"Model created successfully!\n\n"
            msg += f"Collection: {collectionName}\n"
            msg += f"Asset Null: {assetNullName}\n"

            # Show variant groups created
            if len(variantGroupNulls) > 0:
                msg += f"\nVariant Groups: {len(variantGroupNulls)}\n"
                for varNum in sorted(variantGroupNulls.keys()):
                    msg += f"  • {variantGroupNulls[varNum].name}\n"

            # Show which transform option was applied
            if self.rb_zeroTransforms.isChecked():
                msg += "\nTransforms: Zeroed"
            elif self.rb_freezeTransforms.isChecked():
                msg += "\nTransforms: Frozen"
            else:
                msg += "\nTransforms: Unchanged"

            # Add export state message if enabled
            if self.chb_createExportState.isChecked():
                msg += "\n\nExport state will be created shortly..."

            msg += f"\n\nProcessed {len(selectedObjects)} object(s):\n"
            msg += "\n".join([f"  - {obj.name}" for obj in selectedObjects[:10]])
            if len(selectedObjects) > 10:
                msg += f"\n  ... and {len(selectedObjects) - 10} more"

            # Show success popup and close dialog
            self.core.popup(msg, title="MH Create Model - Success", severity="info")
            self.close()

            # Step 9: Schedule export state creation after dialog closes (1 second delay)
            if self.chb_createExportState.isChecked():
                print("Scheduling export state creation for 1 second from now...")
                # Store references to avoid garbage collection
                core = self.core

                # Create standalone function for timer
                def create_state_deferred():
                    print("Creating export state (deferred)...")
                    try:
                        createExportStateStandalone(core, assetName, collectionName)
                    except Exception as e:
                        print(f"Error in timer callback: {e}")
                        import traceback
                        traceback.print_exc()
                    return None  # Unregister timer

                # Register the timer
                bpy.app.timers.register(create_state_deferred, first_interval=1.0)

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

        # Get current preset category and tags
        currentCategory = self.cb_presetCategory.currentText()
        tags = self.presetCategories.get(currentCategory, [])

        # Add objects to the table (avoid duplicates)
        addedCount = 0
        for obj in validObjects:
            if obj not in self.objects:
                self.objects.append(obj)

                # Add row to table
                row = self.tw_objects.rowCount()
                self.tw_objects.insertRow(row)

                # Add object name to first column
                nameItem = QTableWidgetItem(obj.name)
                nameItem.setFlags(nameItem.flags() & ~Qt.ItemIsEditable)  # Make read-only
                self.tw_objects.setItem(row, 0, nameItem)

                # Add description line edit to second column (use dialog's description field as default)
                descLineEdit = QLineEdit()
                descLineEdit.setText(self.e_description.text().strip())
                descLineEdit.setToolTip("Descripción para este objeto")
                descLineEdit.textChanged.connect(self.updatePreview)  # Update preview when description changes
                self.tw_objects.setCellWidget(row, 1, descLineEdit)

                # Add variant spinbox to third column
                variantSpinBox = QSpinBox()
                variantSpinBox.setMinimum(1)
                variantSpinBox.setMaximum(9999)
                variantSpinBox.setValue(self.sb_variantNumber.value())  # Use global variant as default
                variantSpinBox.setToolTip("Número de variante para este objeto")
                variantSpinBox.valueChanged.connect(self.updatePreview)  # Update preview when variant changes
                self.tw_objects.setCellWidget(row, 2, variantSpinBox)

                # Add tag dropdown to fourth column
                tagCombo = QComboBox()
                if currentCategory != "None" and tags:
                    tagCombo.addItem("")  # Empty option
                    tagCombo.addItems(tags)
                else:
                    tagCombo.addItem("")  # Only empty option when None selected

                tagCombo.currentTextChanged.connect(self.updatePreview)  # Update preview when tag changes
                self.tw_objects.setCellWidget(row, 3, tagCombo)

                addedCount += 1
                print(f"DEBUG: Added {obj.name} to table")
            else:
                print(f"DEBUG: {obj.name} already in list, skipping")

        print(f"DEBUG: Added {addedCount} objects. Total objects in list: {len(self.objects)}")
        print(f"DEBUG: Table widget row count: {self.tw_objects.rowCount()}")

    def rcObjects(self, pos):
        """Right-click context menu for object table"""
        row = self.tw_objects.rowAt(pos.y())

        if row == -1:
            self.tw_objects.clearSelection()

        createMenu = QMenu()

        if row != -1:
            actRemove = QAction("Remove", self)
            actRemove.triggered.connect(self.removeSelectedItems)
            createMenu.addAction(actRemove)

        actClear = QAction("Clear", self)
        actClear.triggered.connect(self.clearItems)
        createMenu.addAction(actClear)

        createMenu.exec_(self.tw_objects.mapToGlobal(pos))

    def removeSelectedItems(self):
        """Remove selected rows from the table"""
        selectedRows = sorted(set(index.row() for index in self.tw_objects.selectedIndexes()), reverse=True)
        for row in selectedRows:
            del self.objects[row]
            self.tw_objects.removeRow(row)

    def clearItems(self):
        """Clear all objects from the table"""
        self.tw_objects.setRowCount(0)
        self.objects = []

    def getObjects(self):
        """Return the list of selected objects with their tags"""
        return self.objects

    def getObjectDescriptions(self):
        """Return a dictionary mapping object indices to their descriptions"""
        descriptions = {}
        for row in range(self.tw_objects.rowCount()):
            descLineEdit = self.tw_objects.cellWidget(row, 1)  # Description is column 1
            if descLineEdit:
                desc = descLineEdit.text().strip()
                if desc:  # Only include non-empty descriptions
                    descriptions[row] = desc
        return descriptions

    def getObjectTags(self):
        """Return a dictionary mapping object indices to their selected tags"""
        tags = {}
        for row in range(self.tw_objects.rowCount()):
            tagCombo = self.tw_objects.cellWidget(row, 3)  # Tag is now column 3
            if tagCombo:
                tag = tagCombo.currentText()
                if tag:  # Only include non-empty tags
                    tags[row] = tag
        return tags

    def getObjectVariants(self):
        """Return a dictionary mapping object indices to their variant numbers"""
        variants = {}
        for row in range(self.tw_objects.rowCount()):
            variantSpinBox = self.tw_objects.cellWidget(row, 2)  # Variant is now column 2
            if variantSpinBox:
                variants[row] = variantSpinBox.value()
        return variants

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


class RenamePlantDialog(QDialog):
    """Dialog for selecting plant part to rename"""

    def __init__(self, core, parent=None):
        super(RenamePlantDialog, self).__init__(parent)
        self.core = core
        self.selectedPart = None
        self.setupUi()

    def setupUi(self):
        self.setWindowTitle("Rename Plant")
        self.resize(200, 350)

        # Set window flags to stay on top
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)

        # Connect to cleanup when dialog is closed
        self.finished.connect(self.onFinished)

        # Main layout
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # Plant part buttons
        plantParts = [
            "frutos",
            "flores",
            "hojas",
            "lianas",
            "tallo",
            "tronco",
            "raices"
        ]

        for part in plantParts:
            btn = QPushButton(part.capitalize())
            btn.setMinimumHeight(35)
            btn.clicked.connect(lambda checked, p=part: self.onPartSelected(p))
            layout.addWidget(btn)

        # Add stretch and cancel button
        layout.addStretch()

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)
        layout.addWidget(self.btn_cancel)

    def onPartSelected(self, part):
        """Handle plant part selection and rename selected objects"""
        import re

        self.selectedPart = part
        print(f"Selected plant part: {part}")

        # Get selected objects from Blender
        try:
            selectedObjects = list(bpy.context.view_layer.objects.selected)
        except AttributeError:
            selectedObjects = [obj for obj in bpy.data.objects if obj.select_get()]

        if not selectedObjects:
            self.core.popup("No objects selected. Please select objects to rename.", title="MH Rename Plant")
            return

        # Pattern to find var### (e.g., var001, var123, etc.)
        pattern = re.compile(r'(.*?)(var\d{3})(.*)')

        renamedCount = 0
        skippedObjects = []

        for obj in selectedObjects:
            # Try to find the var### pattern in the object name
            match = pattern.match(obj.name)

            if match:
                # Extract the prefix (everything before var###)
                prefix = match.group(1) + match.group(2)  # Keep prefix + var###

                # Build new name: prefix_partName
                newObjectName = f"{prefix}_{part}"

                # Check if the new name already exists
                if bpy.data.objects.get(newObjectName):
                    print(f"Skipped {obj.name}: Name '{newObjectName}' already exists")
                    skippedObjects.append(obj.name)
                    continue

                # Rename the object
                oldName = obj.name
                obj.name = newObjectName
                print(f"Renamed object: {oldName} -> {newObjectName}")

                # Rename the mesh/curve data
                if obj.type == 'MESH' and obj.data:
                    obj.data.name = f"{newObjectName}_Mesh"
                    print(f"Renamed mesh data to: {obj.data.name}")
                elif obj.type == 'CURVE' and obj.data:
                    obj.data.name = f"{newObjectName}_Curve"
                    print(f"Renamed curve data to: {obj.data.name}")

                renamedCount += 1
            else:
                print(f"Skipped {obj.name}: No var### pattern found")
                skippedObjects.append(obj.name)

        # Show results
        if renamedCount > 0:
            msg = f"Successfully renamed {renamedCount} object(s) to use '{part}'."
            if skippedObjects:
                msg += f"\n\nSkipped {len(skippedObjects)} object(s):"
                msg += "\n" + "\n".join([f"  - {name}" for name in skippedObjects[:10]])
                if len(skippedObjects) > 10:
                    msg += f"\n  ... and {len(skippedObjects) - 10} more"
            self.core.popup(msg, title="MH Rename Plant - Success", severity="info")
        else:
            msg = "No objects were renamed."
            if skippedObjects:
                msg += f"\n\nReasons:\n- No var### pattern found\n- Name already exists"
                msg += f"\n\nSkipped objects:\n"
                msg += "\n".join([f"  - {name}" for name in skippedObjects[:10]])
                if len(skippedObjects) > 10:
                    msg += f"\n  ... and {len(skippedObjects) - 10} more"
            self.core.popup(msg, title="MH Rename Plant")

        self.accept()

    def getSelectedPart(self):
        """Return the selected plant part"""
        return self.selectedPart

    def onFinished(self):
        """Cleanup when dialog is closed"""
        global _active_dialogs
        if self in _active_dialogs:
            _active_dialogs.remove(self)


class MH_RenamePlant(bpy.types.Operator):
    """Rename Plant using MH pipeline"""
    bl_idname = "object.mh_rename_plant"
    bl_label = "Rename Plant"

    def execute(self, context):
        global _active_dialogs

        try:
            # Open RenamePlantDialog
            dialog = RenamePlantDialog(core=pcore)
            pcore.parentWindow(dialog)

            # Keep reference to prevent garbage collection
            _active_dialogs.append(dialog)

            result = dialog.exec_()

            if result == QDialog.Accepted:
                print("Rename Plant completed successfully")
            else:
                print("Rename Plant dialog cancelled")

        except Exception as e:
            import traceback
            print(f"ERROR - MH_RenamePlant - {str(e)}")
            print(traceback.format_exc())
            pcore.popup(f"Error: {str(e)}", title="MH Rename Plant Error")

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
