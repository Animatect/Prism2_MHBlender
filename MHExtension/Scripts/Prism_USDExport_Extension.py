# -*- coding: utf-8 -*-
#
# Prism USD Export Extension
# Extends the default Export state to support USD file export in Blender
#

name = "USDExportExtension"
classname = "USDExportExtension"

from qtpy.QtWidgets import *
from qtpy.QtCore import *


class USDExportExtension:
    def __init__(self, core):
        self.core = core
        self.version = "v1.0.0"

        # Register callbacks to extend the Export state
        # Use lower priority than 50 to ensure this runs after the state is initialized
        self.core.registerCallback("onStateStartup", self.onStateStartup, plugin=self, priority=40)
        self.core.registerCallback("onStateGetSettings", self.onStateGetSettings, plugin=self)
        self.core.registerCallback("onStateSettingsLoaded", self.onStateSettingsLoaded, plugin=self)
        self.core.registerCallback("preExport", self.preExport, plugin=self)
        self.core.registerCallback("postExport", self.postExport, plugin=self)
        self.core.registerCallback("onPluginLoaded", self.onPluginLoaded, plugin=self)

    def onPluginLoaded(self, plugin):
        """
        Called when a plugin is loaded. We use this to add USD to Blender's output formats
        and monkey-patch the export function.
        """
        if plugin.pluginName != "Blender":
            return

        # Add USD formats to Blender's output formats if not already present
        if hasattr(plugin, "outputFormats"):
            usd_formats = [".usd", ".usda", ".usdc"]
            for fmt in usd_formats:
                if fmt not in plugin.outputFormats:
                    plugin.outputFormats.append(fmt)
            print("[USD Export] Added USD formats to Blender output formats")

        # Monkey-patch the export function to handle USD exports
        original_export = plugin.sm_export_exportAppObjects

        def sm_export_exportAppObjects_withUSD(origin, startFrame, endFrame, outputName):
            """Extended export function that handles USD files"""
            # Check if this is a USD export
            if outputName.lower().endswith((".usd", ".usda", ".usdc")):
                return self.exportUSD(origin, startFrame, endFrame, outputName)
            else:
                # Use original export for non-USD formats
                return original_export(origin, startFrame, endFrame, outputName)

        # Replace the export function
        plugin.sm_export_exportAppObjects = sm_export_exportAppObjects_withUSD
        print("[USD Export] Monkey-patched Blender export function for USD support")

    def onStateStartup(self, state):
        """
        This function is called when a state is created.
        We add USD-specific settings to Export states in Blender.
        """
        # Only add USD settings to Export states
        if state.className != "Export":
            return

        # Only add USD settings in Blender
        if self.core.appPlugin.pluginName != "Blender":
            return

        # Get the layout where we'll add our USD settings
        # We'll add it to the general groupbox layout
        lo = state.gb_general.layout()

        # Create a collapsible groupbox for USD settings
        state.gb_usd = QGroupBox("USD Export Settings")
        state.gb_usd.setCheckable(False)
        state.lo_usd = QVBoxLayout(state.gb_usd)

        # Only show USD settings when USD is selected as output type
        state.gb_usd.setVisible(False)

        # USD Export Format (ASCII vs Binary)
        state.w_usdFormat = QWidget()
        state.lo_usdFormat = QHBoxLayout(state.w_usdFormat)
        state.lo_usdFormat.setContentsMargins(9, 0, 9, 0)
        state.l_usdFormat = QLabel("USD Format:")
        state.cb_usdFormat = QComboBox()
        state.cb_usdFormat.addItems(["Binary (usdc)", "ASCII (usda)"])
        state.cb_usdFormat.setToolTip("Choose between binary (.usdc) or ASCII (.usda) format")
        state.lo_usdFormat.addWidget(state.l_usdFormat)
        state.lo_usdFormat.addStretch()
        state.lo_usdFormat.addWidget(state.cb_usdFormat)
        state.lo_usd.addWidget(state.w_usdFormat)

        # Export Materials
        state.w_usdMaterials = QWidget()
        state.lo_usdMaterials = QHBoxLayout(state.w_usdMaterials)
        state.lo_usdMaterials.setContentsMargins(9, 0, 9, 0)
        state.l_usdMaterials = QLabel("Export Materials:")
        state.chb_usdMaterials = QCheckBox()
        state.chb_usdMaterials.setChecked(True)
        state.chb_usdMaterials.setToolTip("Export material assignments and shader networks")
        state.lo_usdMaterials.addWidget(state.l_usdMaterials)
        state.lo_usdMaterials.addStretch()
        state.lo_usdMaterials.addWidget(state.chb_usdMaterials)
        state.lo_usd.addWidget(state.w_usdMaterials)

        # Export UVMaps
        state.w_usdUVMaps = QWidget()
        state.lo_usdUVMaps = QHBoxLayout(state.w_usdUVMaps)
        state.lo_usdUVMaps.setContentsMargins(9, 0, 9, 0)
        state.l_usdUVMaps = QLabel("Export UV Maps:")
        state.chb_usdUVMaps = QCheckBox()
        state.chb_usdUVMaps.setChecked(True)
        state.chb_usdUVMaps.setToolTip("Export UV coordinate maps")
        state.lo_usdUVMaps.addWidget(state.l_usdUVMaps)
        state.lo_usdUVMaps.addStretch()
        state.lo_usdUVMaps.addWidget(state.chb_usdUVMaps)
        state.lo_usd.addWidget(state.w_usdUVMaps)

        # Export Normals
        state.w_usdNormals = QWidget()
        state.lo_usdNormals = QHBoxLayout(state.w_usdNormals)
        state.lo_usdNormals.setContentsMargins(9, 0, 9, 0)
        state.l_usdNormals = QLabel("Export Normals:")
        state.chb_usdNormals = QCheckBox()
        state.chb_usdNormals.setChecked(True)
        state.chb_usdNormals.setToolTip("Export mesh normals")
        state.lo_usdNormals.addWidget(state.l_usdNormals)
        state.lo_usdNormals.addStretch()
        state.lo_usdNormals.addWidget(state.chb_usdNormals)
        state.lo_usd.addWidget(state.w_usdNormals)

        # Export Animations
        state.w_usdAnimation = QWidget()
        state.lo_usdAnimation = QHBoxLayout(state.w_usdAnimation)
        state.lo_usdAnimation.setContentsMargins(9, 0, 9, 0)
        state.l_usdAnimation = QLabel("Export Animation:")
        state.chb_usdAnimation = QCheckBox()
        state.chb_usdAnimation.setChecked(True)
        state.chb_usdAnimation.setToolTip("Export animated transforms and deformations")
        state.lo_usdAnimation.addWidget(state.l_usdAnimation)
        state.lo_usdAnimation.addStretch()
        state.lo_usdAnimation.addWidget(state.chb_usdAnimation)
        state.lo_usd.addWidget(state.w_usdAnimation)

        # Export Hair/Curves
        state.w_usdHair = QWidget()
        state.lo_usdHair = QHBoxLayout(state.w_usdHair)
        state.lo_usdHair.setContentsMargins(9, 0, 9, 0)
        state.l_usdHair = QLabel("Export Hair/Curves:")
        state.chb_usdHair = QCheckBox()
        state.chb_usdHair.setChecked(False)
        state.chb_usdHair.setToolTip("Export hair particle systems and curves as USD curves")
        state.lo_usdHair.addWidget(state.l_usdHair)
        state.lo_usdHair.addStretch()
        state.lo_usdHair.addWidget(state.chb_usdHair)
        state.lo_usd.addWidget(state.w_usdHair)

        # Use Instancing
        state.w_usdInstancing = QWidget()
        state.lo_usdInstancing = QHBoxLayout(state.w_usdInstancing)
        state.lo_usdInstancing.setContentsMargins(9, 0, 9, 0)
        state.l_usdInstancing = QLabel("Use Instancing:")
        state.chb_usdInstancing = QCheckBox()
        state.chb_usdInstancing.setChecked(True)
        state.chb_usdInstancing.setToolTip("Export instances where possible for better performance")
        state.lo_usdInstancing.addWidget(state.l_usdInstancing)
        state.lo_usdInstancing.addStretch()
        state.lo_usdInstancing.addWidget(state.chb_usdInstancing)
        state.lo_usd.addWidget(state.w_usdInstancing)

        # Evaluation Mode
        state.w_usdEvalMode = QWidget()
        state.lo_usdEvalMode = QHBoxLayout(state.w_usdEvalMode)
        state.lo_usdEvalMode.setContentsMargins(9, 0, 9, 0)
        state.l_usdEvalMode = QLabel("Evaluation Mode:")
        state.cb_usdEvalMode = QComboBox()
        state.cb_usdEvalMode.addItems(["Viewport", "Render"])
        state.cb_usdEvalMode.setCurrentIndex(1)  # Default to Render
        state.cb_usdEvalMode.setToolTip("Use viewport or render settings for object evaluation")
        state.lo_usdEvalMode.addWidget(state.l_usdEvalMode)
        state.lo_usdEvalMode.addStretch()
        state.lo_usdEvalMode.addWidget(state.cb_usdEvalMode)
        state.lo_usd.addWidget(state.w_usdEvalMode)

        # Add the USD groupbox to the main layout
        lo.addWidget(state.gb_usd)

        # Save settings when any USD option changes
        state.cb_usdFormat.currentIndexChanged.connect(lambda: state.stateManager.saveStatesToScene())
        state.chb_usdMaterials.toggled.connect(lambda: state.stateManager.saveStatesToScene())
        state.chb_usdUVMaps.toggled.connect(lambda: state.stateManager.saveStatesToScene())
        state.chb_usdNormals.toggled.connect(lambda: state.stateManager.saveStatesToScene())
        state.chb_usdAnimation.toggled.connect(lambda: state.stateManager.saveStatesToScene())
        state.chb_usdHair.toggled.connect(lambda: state.stateManager.saveStatesToScene())
        state.chb_usdInstancing.toggled.connect(lambda: state.stateManager.saveStatesToScene())
        state.cb_usdEvalMode.currentIndexChanged.connect(lambda: state.stateManager.saveStatesToScene())

        # Connect to the output type change to show/hide USD settings
        state.cb_outType.currentIndexChanged.connect(lambda: self.updateUSDVisibility(state))

        # Initial visibility update
        self.updateUSDVisibility(state)

    def updateUSDVisibility(self, state):
        """Show/hide USD settings based on selected output type"""
        outputType = state.getOutputType()
        # Show USD settings if output type contains "usd"
        isUSD = outputType.lower() in [".usd", ".usda", ".usdc"]
        if hasattr(state, "gb_usd"):
            state.gb_usd.setVisible(isUSD)

    def onStateGetSettings(self, state, settings):
        """
        Save USD settings to the state data
        """
        if state.className != "Export":
            return

        if self.core.appPlugin.pluginName != "Blender":
            return

        # Only save USD settings if they exist on this state
        if hasattr(state, "cb_usdFormat"):
            settings["usd_format"] = state.cb_usdFormat.currentText()
            settings["usd_materials"] = state.chb_usdMaterials.isChecked()
            settings["usd_uvmaps"] = state.chb_usdUVMaps.isChecked()
            settings["usd_normals"] = state.chb_usdNormals.isChecked()
            settings["usd_animation"] = state.chb_usdAnimation.isChecked()
            settings["usd_hair"] = state.chb_usdHair.isChecked()
            settings["usd_instancing"] = state.chb_usdInstancing.isChecked()
            settings["usd_eval_mode"] = state.cb_usdEvalMode.currentText()

    def onStateSettingsLoaded(self, state, settings):
        """
        Load USD settings from saved state data
        """
        if state.className != "Export":
            return

        if self.core.appPlugin.pluginName != "Blender":
            return

        # Only load USD settings if they exist in the saved data and on the state
        if hasattr(state, "cb_usdFormat"):
            if "usd_format" in settings:
                idx = state.cb_usdFormat.findText(settings["usd_format"])
                if idx != -1:
                    state.cb_usdFormat.setCurrentIndex(idx)

            if "usd_materials" in settings:
                state.chb_usdMaterials.setChecked(settings["usd_materials"])

            if "usd_uvmaps" in settings:
                state.chb_usdUVMaps.setChecked(settings["usd_uvmaps"])

            if "usd_normals" in settings:
                state.chb_usdNormals.setChecked(settings["usd_normals"])

            if "usd_animation" in settings:
                state.chb_usdAnimation.setChecked(settings["usd_animation"])

            if "usd_hair" in settings:
                state.chb_usdHair.setChecked(settings["usd_hair"])

            if "usd_instancing" in settings:
                state.chb_usdInstancing.setChecked(settings["usd_instancing"])

            if "usd_eval_mode" in settings:
                idx = state.cb_usdEvalMode.findText(settings["usd_eval_mode"])
                if idx != -1:
                    state.cb_usdEvalMode.setCurrentIndex(idx)

    def preExport(self, **kwargs):
        """
        This function is called before the export starts.
        We can perform USD-specific preparations here.
        """
        state = kwargs.get("state")
        if not state or state.className != "Export":
            return

        if self.core.appPlugin.pluginName != "Blender":
            return

        outputPath = kwargs.get("outputpath", "")

        # Check if this is a USD export
        if not outputPath.lower().endswith((".usd", ".usda", ".usdc")):
            return

        # Log USD export start
        print(f"[USD Export] Starting USD export to: {outputPath}")

    def postExport(self, **kwargs):
        """
        This function is called after the export completes.
        We can perform USD-specific post-processing here.
        """
        state = kwargs.get("state")
        if not state or state.className != "Export":
            return

        if self.core.appPlugin.pluginName != "Blender":
            return

        outputPath = kwargs.get("outputpath", "")

        # Check if this was a USD export
        if not outputPath.lower().endswith((".usd", ".usda", ".usdc")):
            return

        # Log USD export completion
        print(f"[USD Export] Completed USD export to: {outputPath}")

    def exportUSD(self, origin, startFrame, endFrame, outputName):
        """
        Export objects to USD format using Blender's USD exporter.

        Args:
            origin: The export state object
            startFrame: Start frame for export
            endFrame: End frame for export
            outputName: Full path to the output USD file

        Returns:
            str: Path to the exported file, or error message
        """
        try:
            import bpy
            import os

            # Get USD settings from the state
            usd_format = "USDC"  # Default to binary
            export_materials = True
            export_uvmaps = True
            export_normals = True
            export_animation = True
            export_hair = False
            use_instancing = True
            evaluation_mode = "RENDER"

            if hasattr(origin, "cb_usdFormat"):
                format_text = origin.cb_usdFormat.currentText()
                if "ASCII" in format_text or "usda" in format_text:
                    usd_format = "USDA"
                else:
                    usd_format = "USDC"

            if hasattr(origin, "chb_usdMaterials"):
                export_materials = origin.chb_usdMaterials.isChecked()

            if hasattr(origin, "chb_usdUVMaps"):
                export_uvmaps = origin.chb_usdUVMaps.isChecked()

            if hasattr(origin, "chb_usdNormals"):
                export_normals = origin.chb_usdNormals.isChecked()

            if hasattr(origin, "chb_usdAnimation"):
                export_animation = origin.chb_usdAnimation.isChecked()

            if hasattr(origin, "chb_usdHair"):
                export_hair = origin.chb_usdHair.isChecked()

            if hasattr(origin, "chb_usdInstancing"):
                use_instancing = origin.chb_usdInstancing.isChecked()

            if hasattr(origin, "cb_usdEvalMode"):
                eval_text = origin.cb_usdEvalMode.currentText()
                evaluation_mode = eval_text.upper()

            # Ensure output directory exists
            output_dir = os.path.dirname(outputName)
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            # Determine what to export
            export_whole_scene = False
            selected_only = True

            if hasattr(origin, "chb_wholeScene") and origin.chb_wholeScene.isChecked():
                export_whole_scene = True
                selected_only = False
            else:
                # Select the objects from the export state
                if hasattr(origin, "nodes") and len(origin.nodes) > 0:
                    # Deselect all
                    bpy.ops.object.select_all(action='DESELECT')

                    # Select the nodes specified in the export state
                    for node in origin.nodes:
                        if self.core.appPlugin.isNodeValid(origin, node):
                            try:
                                obj = bpy.data.objects.get(node)
                                if obj:
                                    obj.select_set(True)
                            except:
                                pass
                    selected_only = True
                else:
                    # No specific objects, export selection or scene
                    selected_only = len(bpy.context.selected_objects) > 0

            # Build USD export parameters
            export_params = {
                'filepath': outputName,
                'selected_objects_only': selected_only,
                'export_materials': export_materials,
                'export_uvmaps': export_uvmaps,
                'export_normals': export_normals,
                'export_hair': export_hair,
                'use_instancing': use_instancing,
                'evaluation_mode': evaluation_mode,
            }

            # Handle animation export
            if export_animation and startFrame != endFrame:
                export_params['export_animation'] = True
                export_params['start_frame'] = int(startFrame)
                export_params['end_frame'] = int(endFrame)
            else:
                export_params['export_animation'] = False

            # Adjust file extension based on format
            if usd_format == "USDA" and not outputName.endswith(".usda"):
                # If user selected ASCII but filename is .usd or .usdc, change extension
                if outputName.endswith(".usd") or outputName.endswith(".usdc"):
                    outputName = os.path.splitext(outputName)[0] + ".usda"
                    export_params['filepath'] = outputName
            elif usd_format == "USDC" and outputName.endswith(".usda"):
                # If user selected binary but filename is .usda, change to .usdc
                outputName = os.path.splitext(outputName)[0] + ".usdc"
                export_params['filepath'] = outputName

            print(f"[USD Export] Exporting to: {outputName}")
            print(f"[USD Export] Format: {usd_format}")
            print(f"[USD Export] Frame range: {startFrame} - {endFrame}")
            print(f"[USD Export] Selected only: {selected_only}")
            print(f"[USD Export] Animation: {export_animation}")

            # Execute the USD export
            result = bpy.ops.wm.usd_export(**export_params)

            if result == {'FINISHED'}:
                print(f"[USD Export] Successfully exported to: {outputName}")
                return outputName
            else:
                error_msg = f"USD export failed with result: {result}"
                print(f"[USD Export] ERROR: {error_msg}")
                return f"Error: {error_msg}"

        except Exception as e:
            import traceback
            error_msg = f"USD export failed: {str(e)}\n{traceback.format_exc()}"
            print(f"[USD Export] ERROR: {error_msg}")
            return f"Error: {str(e)}"
