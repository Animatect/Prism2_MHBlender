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


class MH_CreateModel(bpy.types.Operator):
    """Create Model using MH pipeline"""
    bl_idname = "object.mh_create_model"
    bl_label = "Create Model"

    def execute(self, context):
        try:
            # Get the current scene filename
            fileName = pcore.getCurrentFileName()

            if not fileName:
                print("No scene file opened")
                pcore.popup("Please open or save a scene file first", title="MH Create Model")
                return {"CANCELLED"}

            # Check if file is in the pipeline
            if not pcore.fileInPipeline(fileName):
                print(f"File is not in pipeline: {fileName}")
                pcore.popup(
                    "This file is not in the Prism pipeline.\n\nPlease use the Project Browser to save your scene with the correct name.",
                    title="MH Create Model"
                )
                return {"CANCELLED"}

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

                # Build info message
                msg = f"Asset Name: {assetName}"
                if assetPath:
                    msg += f"\nAsset Path: {assetPath}"
                if pathData.get("department"):
                    msg += f"\nDepartment: {pathData.get('department')}"
                if pathData.get("task"):
                    msg += f"\nTask: {pathData.get('task')}"
                if pathData.get("version"):
                    msg += f"\nVersion: {pathData.get('version')}"

                pcore.popup(msg, title="MH Create Model - Asset Info")

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
