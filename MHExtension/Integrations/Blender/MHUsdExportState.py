# -*- coding: utf-8 -*-
#
# MH USD Export State Functions
# Handles all USD export state customization for Blender
#

from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *

from PrismUtils.Decorators import err_catcher


class MHUsdExportState:
    """
    Handles USD export state customization for Blender.
    This class provides UI extensions and logic for .mhUsd export format.
    """

    def __init__(self, core):
        self.core = core

    @err_catcher(name=__name__)
    def onStateStartup(self, state):
        """Add custom USD export settings to export states when .mhUsd is selected"""
        # Only for export states
        if state.className != "Export":
            return

        # Only in Blender
        if self.core.appPlugin.pluginName != "Blender":
            return

        # Get the layout to add widgets to
        lo = state.gb_export.layout()

        # Create USD Format Settings GroupBox
        state.gb_mhUsd = QGroupBox("USD Format Settings")
        state.gb_mhUsd.setCheckable(False)
        state.lo_mhUsd = QVBoxLayout(state.gb_mhUsd)

        # USD Format dropdown (usd, usdc, usda)
        state.w_usdFormat = QWidget()
        state.lo_usdFormat = QHBoxLayout(state.w_usdFormat)
        state.lo_usdFormat.setContentsMargins(9, 0, 9, 0)
        state.l_usdFormat = QLabel("USD Format:")
        state.cb_usdFormat = QComboBox()
        state.cb_usdFormat.setMinimumWidth(150)
        state.cb_usdFormat.addItems(["usd", "usdc", "usda"])
        state.cb_usdFormat.setCurrentText("usd")
        state.lo_usdFormat.addWidget(state.l_usdFormat)
        state.lo_usdFormat.addStretch()
        state.lo_usdFormat.addWidget(state.cb_usdFormat)
        state.lo_mhUsd.addWidget(state.w_usdFormat)
        state.cb_usdFormat.currentIndexChanged.connect(lambda: state.stateManager.saveStatesToScene())

        # Object Types section
        state.w_objectTypes = QWidget()
        state.lo_objectTypes = QVBoxLayout(state.w_objectTypes)
        state.lo_objectTypes.setContentsMargins(9, 0, 9, 0)
        state.l_objectTypes = QLabel("Object Types:")
        state.l_objectTypes.setStyleSheet("font-weight: bold;")
        state.lo_objectTypes.addWidget(state.l_objectTypes)

        # Checkboxes for object types
        state.chb_exportMeshes = QCheckBox("Meshes")
        state.chb_exportMeshes.setChecked(True)  # Default: ON
        state.chb_exportLights = QCheckBox("Lights")
        state.chb_exportLights.setChecked(False)  # Default: OFF
        state.chb_exportCameras = QCheckBox("Cameras")
        state.chb_exportCameras.setChecked(False)  # Default: OFF
        state.chb_exportCurves = QCheckBox("Curves")
        state.chb_exportCurves.setChecked(True)  # Default: ON
        state.chb_exportPointClouds = QCheckBox("Point Clouds")
        state.chb_exportPointClouds.setChecked(False)  # Default: OFF
        state.chb_exportVolumes = QCheckBox("Volumes")
        state.chb_exportVolumes.setChecked(False)  # Default: OFF

        state.lo_objectTypes.addWidget(state.chb_exportMeshes)
        state.lo_objectTypes.addWidget(state.chb_exportLights)
        state.lo_objectTypes.addWidget(state.chb_exportCameras)
        state.lo_objectTypes.addWidget(state.chb_exportCurves)
        state.lo_objectTypes.addWidget(state.chb_exportPointClouds)
        state.lo_objectTypes.addWidget(state.chb_exportVolumes)

        state.lo_mhUsd.addWidget(state.w_objectTypes)

        # Connect checkboxes to save
        state.chb_exportMeshes.toggled.connect(lambda: state.stateManager.saveStatesToScene())
        state.chb_exportLights.toggled.connect(lambda: state.stateManager.saveStatesToScene())
        state.chb_exportCameras.toggled.connect(lambda: state.stateManager.saveStatesToScene())
        state.chb_exportCurves.toggled.connect(lambda: state.stateManager.saveStatesToScene())
        state.chb_exportPointClouds.toggled.connect(lambda: state.stateManager.saveStatesToScene())
        state.chb_exportVolumes.toggled.connect(lambda: state.stateManager.saveStatesToScene())

        # Geometry section
        state.w_geometry = QWidget()
        state.lo_geometry = QVBoxLayout(state.w_geometry)
        state.lo_geometry.setContentsMargins(9, 0, 9, 0)
        state.l_geometry = QLabel("Geometry:")
        state.l_geometry.setStyleSheet("font-weight: bold;")
        state.lo_geometry.addWidget(state.l_geometry)

        state.chb_renameUVMaps = QCheckBox("Rename UV Maps")
        state.chb_renameUVMaps.setChecked(True)  # Default: ON
        state.lo_geometry.addWidget(state.chb_renameUVMaps)
        state.chb_renameUVMaps.toggled.connect(lambda: state.stateManager.saveStatesToScene())

        state.lo_mhUsd.addWidget(state.w_geometry)

        # Materials section
        state.w_materials = QWidget()
        state.lo_materials = QVBoxLayout(state.w_materials)
        state.lo_materials.setContentsMargins(9, 0, 9, 0)
        state.l_materials = QLabel("Materials:")
        state.l_materials.setStyleSheet("font-weight: bold;")
        state.lo_materials.addWidget(state.l_materials)

        state.chb_exportMaterials = QCheckBox("Export Materials")
        state.chb_exportMaterials.setChecked(False)  # Default: OFF
        state.lo_materials.addWidget(state.chb_exportMaterials)
        state.chb_exportMaterials.toggled.connect(lambda: state.stateManager.saveStatesToScene())

        state.lo_mhUsd.addWidget(state.w_materials)

        # Instancing section
        state.w_instancing = QWidget()
        state.lo_instancing = QVBoxLayout(state.w_instancing)
        state.lo_instancing.setContentsMargins(9, 0, 9, 0)
        state.l_instancing = QLabel("Instancing:")
        state.l_instancing.setStyleSheet("font-weight: bold;")
        state.lo_instancing.addWidget(state.l_instancing)

        state.chb_exportInstancing = QCheckBox("Export Instancing")
        state.chb_exportInstancing.setChecked(False)  # Default: OFF
        state.lo_instancing.addWidget(state.chb_exportInstancing)
        state.chb_exportInstancing.toggled.connect(lambda: state.stateManager.saveStatesToScene())

        state.lo_mhUsd.addWidget(state.w_instancing)

        # Add the USD settings group to the main layout
        lo.addWidget(state.gb_mhUsd)

        # Initially hide the USD settings (only show when .mhUsd is selected)
        state.gb_mhUsd.setVisible(False)

        # Connect to output type change to show/hide USD settings
        if hasattr(state, 'cb_outType'):
            state.cb_outType.currentTextChanged.connect(lambda text: self.onOutputTypeChanged(state, text))

    @err_catcher(name=__name__)
    def onOutputTypeChanged(self, state, outputType):
        """Show/hide USD settings based on selected output type"""
        if hasattr(state, 'gb_mhUsd'):
            state.gb_mhUsd.setVisible(outputType == ".mhUsd")

    @err_catcher(name=__name__)
    def onStateGetSettings(self, state, settings):
        """Collect USD export settings for saving"""
        if state.className != "Export":
            return

        if hasattr(state, 'gb_mhUsd'):
            settings["mhUsd_format"] = state.cb_usdFormat.currentText()
            settings["mhUsd_exportMeshes"] = state.chb_exportMeshes.isChecked()
            settings["mhUsd_exportLights"] = state.chb_exportLights.isChecked()
            settings["mhUsd_exportCameras"] = state.chb_exportCameras.isChecked()
            settings["mhUsd_exportCurves"] = state.chb_exportCurves.isChecked()
            settings["mhUsd_exportPointClouds"] = state.chb_exportPointClouds.isChecked()
            settings["mhUsd_exportVolumes"] = state.chb_exportVolumes.isChecked()
            settings["mhUsd_renameUVMaps"] = state.chb_renameUVMaps.isChecked()
            settings["mhUsd_exportMaterials"] = state.chb_exportMaterials.isChecked()
            settings["mhUsd_exportInstancing"] = state.chb_exportInstancing.isChecked()

    @err_catcher(name=__name__)
    def onStateSettingsLoaded(self, state, settings):
        """Load USD export settings from saved data"""
        if state.className != "Export":
            return

        if hasattr(state, 'gb_mhUsd'):
            if "mhUsd_format" in settings:
                idx = state.cb_usdFormat.findText(settings["mhUsd_format"])
                if idx != -1:
                    state.cb_usdFormat.setCurrentIndex(idx)

            if "mhUsd_exportMeshes" in settings:
                state.chb_exportMeshes.setChecked(settings["mhUsd_exportMeshes"])
            if "mhUsd_exportLights" in settings:
                state.chb_exportLights.setChecked(settings["mhUsd_exportLights"])
            if "mhUsd_exportCameras" in settings:
                state.chb_exportCameras.setChecked(settings["mhUsd_exportCameras"])
            if "mhUsd_exportCurves" in settings:
                state.chb_exportCurves.setChecked(settings["mhUsd_exportCurves"])
            if "mhUsd_exportPointClouds" in settings:
                state.chb_exportPointClouds.setChecked(settings["mhUsd_exportPointClouds"])
            if "mhUsd_exportVolumes" in settings:
                state.chb_exportVolumes.setChecked(settings["mhUsd_exportVolumes"])
            if "mhUsd_renameUVMaps" in settings:
                state.chb_renameUVMaps.setChecked(settings["mhUsd_renameUVMaps"])
            if "mhUsd_exportMaterials" in settings:
                state.chb_exportMaterials.setChecked(settings["mhUsd_exportMaterials"])
            if "mhUsd_exportInstancing" in settings:
                state.chb_exportInstancing.setChecked(settings["mhUsd_exportInstancing"])

            # Update visibility based on current output type
            if hasattr(state, 'cb_outType'):
                self.onOutputTypeChanged(state, state.cb_outType.currentText())
