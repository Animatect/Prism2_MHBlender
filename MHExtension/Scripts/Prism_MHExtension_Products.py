# -*- coding: utf-8 -*-
#
# MH Extension - Product Management
# Handles product browser customization and ASSET grouping logic
#

import os
import inspect
import logging
import shutil
import platform
import errno

from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *

from PrismUtils.Decorators import err_catcher

logger = logging.getLogger(__name__)


class Prism_MHExtension_Products:
    """
    Handles product browser customization for the MH Extension.
    Manages ASSET grouping, usdlayer grouping, and custom icons.
    """

    def __init__(self, core, plugin):
        self.core = core
        self.plugin = plugin

        # Path to custom icons (relative to this file)
        self.iconsPath = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "Integrations",
            "Icons"
        )

    @err_catcher(name=__name__)
    def onProductBrowserOpen(self, productBrowser):
        """
        Callback when ProductBrowser opens. Monkey patches the updateIdentifiers method
        to automatically group usdlayer_* products under ASSET products.
        ASSET will appear as both a selectable product AND a group containing usdlayer items.
        """
        logger.debug("ProductBrowser opened - applying ASSET grouping logic")

        # Store the original updateIdentifiers method
        original_updateIdentifiers = productBrowser.updateIdentifiers
        # Store the original createGroupItems method
        original_createGroupItems = productBrowser.createGroupItems

        # Wrapper for createGroupItems to handle ASSET as both item and group
        def custom_createGroupItems(identifiers):
            # Call original method to get groups and group items
            groups, groupItems = original_createGroupItems(identifiers)

            # Find if ASSET exists and if there are usdlayer_* products grouped under it
            if "ASSET" in groupItems and "ASSET" in identifiers:
                # Replace the group-only item with a hybrid item
                assetGroupItem = groupItems["ASSET"]
                assetData = identifiers["ASSET"]

                # Clear the "isGroup" flag and add the actual product data
                assetGroupItem.setData(0, Qt.UserRole, assetData)

                # Update the display text to show it's a product (remove folder-only appearance)
                assetGroupItem.setText(0, "ASSET")

                # Set custom icon for ASSET
                iconPath = os.path.join(self.iconsPath, "addasset.svg")
                if os.path.exists(iconPath):
                    icon = self.core.media.getColoredIcon(iconPath)
                    assetGroupItem.setIcon(0, icon)
                    logger.debug(f"Set custom icon for ASSET from: {iconPath}")
                else:
                    logger.warning(f"ASSET icon not found at: {iconPath}")

                logger.debug("Modified ASSET to be both group and selectable product")

            return groups, groupItems

        # Create wrapper function that adds our custom grouping logic
        def custom_updateIdentifiers(item=None, restoreSelection=False):
            # Get all identifiers before modification
            identifiers = productBrowser.getIdentifiers()

            # Auto-group usdlayer_* products under ASSET
            hasUsdLayers = False
            for identifierName in list(identifiers.keys()):
                # Check if this is a usdlayer_* product
                if identifierName.startswith("usdlayer_"):
                    hasUsdLayers = True
                    # Check if ASSET product exists in the same entity
                    if "ASSET" in identifiers:
                        # Set the group for this usdlayer product
                        self.core.products.setProductsGroup(
                            [identifiers[identifierName]],
                            group="ASSET"
                        )
                        logger.debug(f"Auto-grouped {identifierName} under ASSET")

            # If ASSET has usdlayer children, mark it as a group to prevent duplicate
            # The custom_createGroupItems will convert it to a hybrid item/group
            if hasUsdLayers and "ASSET" in identifiers:
                # Mark ASSET as a group so it won't appear as a standalone item
                # It will only appear through the group item created in custom_createGroupItems
                self.core.products.setProductsGroup(
                    [identifiers["ASSET"]],
                    group="ASSET"  # Group it under itself
                )
                logger.debug("Marked ASSET as group to prevent duplicate display")

            # Call the original updateIdentifiers method
            # Handle both function signatures (with or without 'item' parameter)
            try:
                sig = inspect.signature(original_updateIdentifiers)
                params = list(sig.parameters.keys())

                # Call with appropriate parameters based on signature
                if 'item' in params:
                    original_updateIdentifiers(item=item, restoreSelection=restoreSelection)
                else:
                    original_updateIdentifiers(restoreSelection=restoreSelection)
            except:
                # Fallback: try calling with just restoreSelection
                try:
                    original_updateIdentifiers(restoreSelection=restoreSelection)
                except:
                    # Last resort: call with no arguments
                    original_updateIdentifiers()

        # Replace both methods with our custom versions
        productBrowser.createGroupItems = custom_createGroupItems
        productBrowser.updateIdentifiers = custom_updateIdentifiers

        logger.debug("Product browser patches applied successfully")

    @err_catcher(name=__name__)
    def getCustomProductIcon(self, productName):
        """
        Get a custom icon for a specific product name.
        Returns None if no custom icon is available.
        """
        iconMapping = {
            "ASSET": "addasset.svg",
            # Add more product-specific icons here
        }

        if productName in iconMapping:
            iconPath = os.path.join(self.iconsPath, iconMapping[productName])
            if os.path.exists(iconPath):
                return self.core.media.getColoredIcon(iconPath)
            else:
                logger.warning(f"Icon not found for {productName} at: {iconPath}")

        return None

    @err_catcher(name=__name__)
    def isGroupableProduct(self, productName):
        """
        Check if a product should be auto-grouped under another product.
        Returns the parent product name if it should be grouped, None otherwise.
        """
        # usdlayer_* products should be grouped under ASSET
        if productName.startswith("usdlayer_"):
            return "ASSET"

        # Add more grouping rules here as needed
        return None

    @err_catcher(name=__name__)
    def updateMasterVersion(self, path):
        """
        Extended updateMasterVersion that creates USD reference files for USD formats
        instead of copying the actual files.

        For .usda, .usdc, or .usd files:
        - If useUsdReferences setting is enabled: Creates a master .usda reference file
        - If useUsdReferences setting is disabled: Uses standard copy/hardlink behavior
        - Copies version info and other metadata files normally

        For all other formats:
        - Calls the original function (standard copy/hardlink behavior)

        Args:
            path: The path to the version file to set as master
        """
        # Get file extension
        _, ext = os.path.splitext(path)
        ext = ext.lower()

        # Check if this is a USD file
        isUsdFile = ext in ['.usda', '.usdc', '.usd']

        # Check user setting for USD reference behavior
        useUsdReferences = self.plugin.getUseUsdReferences() if hasattr(self.plugin, 'getUseUsdReferences') else True

        if not isUsdFile or not useUsdReferences:
            # Not a USD file OR user disabled USD reference mode - use original behavior
            reason = f"Non-USD file {ext}" if not isUsdFile else f"USD references disabled in settings"
            logger.debug(f"{reason}, using original updateMasterVersion")
            return self.core.plugins.callUnpatchedFunction(
                self.core.products.updateMasterVersion, path
            )

        logger.debug(f"USD file detected ({ext}), creating reference-based master version")

        # ===== USD-specific master version creation =====

        # Get source file data
        data = self.core.paths.getCachePathData(path)

        forcedLoc = os.getenv("PRISM_PRODUCT_MASTER_LOC")
        if forcedLoc:
            location = forcedLoc
        else:
            location = self.core.products.getLocationFromFilepath(path)

        origVersion = data.get("version")
        if not origVersion:
            msg = "Invalid product version. Make sure the version contains valid files."
            self.core.popup(msg)
            return

        data["type"] = self.core.paths.getEntityTypeFromPath(path)

        # Generate master path - force .usda extension for master file
        masterPath = self.core.products.generateProductPath(
            entity=data,
            task=data.get("product"),
            extension=".usda",  # Always use .usda for master reference files
            version="master",
            location=location,
        )

        if masterPath:
            logger.debug("updating USD master version: %s from %s" % (masterPath, path))
        else:
            logger.warning("failed to generate masterpath: %s %s" % (data, location))
            msg = "Failed to generate masterpath. Please contact the support."
            self.core.popup(msg)
            return

        # Delete existing master version
        msg = "Failed to update master version. Couldn't remove old master version.\n\n%s"
        result = self.core.products.deleteMasterVersion(masterPath, msg)
        if not result:
            return

        # Create master directory
        if not os.path.exists(os.path.dirname(masterPath)):
            try:
                os.makedirs(os.path.dirname(masterPath))
            except Exception as e:
                if e.errno != errno.EEXIST:
                    raise

        # Calculate relative path from master to versioned file
        masterDir = os.path.dirname(masterPath)
        versionedDir = os.path.dirname(path)
        relPath = os.path.relpath(path, masterDir).replace("\\", "/")

        # Extract entity name and product name for defaultPrim
        entityName = data.get("asset") or data.get("shot", "")
        productName = data.get("product", "")

        # Create the defaultPrim name (e.g., "chartoOmit" or "configure_geo_layer")
        if productName.startswith("usdlayer_"):
            # For usdlayer products, use format: configure_{layertype}_layer
            layerType = productName.replace("usdlayer_", "")
            defaultPrim = f"configure_{layerType}_layer"
        else:
            # For regular products, use entity name
            defaultPrim = entityName

        # Read metadata from source file if it exists (for proper metadata)
        metadata = self._extractUsdMetadata(path)

        # Create USD reference file content
        usdContent = self._generateUsdReferenceFile(
            relPath=relPath,
            defaultPrim=defaultPrim,
            metadata=metadata,
            sourceVersion=origVersion
        )

        # Write the USD reference file
        try:
            with open(masterPath, 'w') as f:
                f.write(usdContent)
            logger.debug(f"Created USD reference master file: {masterPath}")
        except Exception as e:
            msg = f"Failed to write USD master file: {e}"
            self.core.popup(msg)
            logger.error(msg)
            return

        # Copy version info files (same as original function)
        folderPath = self.core.products.getVersionInfoPathFromProductFilepath(path)
        infoPath = self.core.getVersioninfoPath(folderPath)
        folderPath = self.core.products.getVersionInfoPathFromProductFilepath(masterPath)
        masterInfoPath = self.core.getVersioninfoPath(folderPath)

        if os.path.exists(infoPath):
            shutil.copy2(infoPath, masterInfoPath)
            logger.debug(f"Copied version info: {infoPath} -> {masterInfoPath}")

        # Update preferredFile in master's version info
        infoData = self.core.getConfig(configPath=infoPath)
        if infoData:
            # Set the master .usda as the preferred file
            newPreferredFile = os.path.basename(masterPath)
            self.core.setConfig("preferredFile", val=newPreferredFile, configPath=masterInfoPath)
            # Store the source version for tracking
            self.core.setConfig("sourceVersion", val=origVersion, configPath=masterInfoPath)
            logger.debug(f"Updated master version info with preferredFile={newPreferredFile}, sourceVersion={origVersion}")

        # Copy additional metadata files (but not the actual USD files)
        processedFiles = [os.path.basename(infoPath), os.path.basename(path)]
        files = os.listdir(os.path.dirname(path))
        for file in files:
            if file in processedFiles:
                continue

            # Skip USD files - we only reference them
            fileExt = os.path.splitext(file)[1].lower()
            if fileExt in ['.usda', '.usdc', '.usd']:
                continue

            filepath = os.path.join(os.path.dirname(path), file)
            fileTargetPath = os.path.join(os.path.dirname(masterPath), file)

            if not os.path.exists(os.path.dirname(fileTargetPath)):
                try:
                    os.makedirs(os.path.dirname(fileTargetPath))
                except:
                    self.core.popup("The directory could not be created: %s" % os.path.dirname(fileTargetPath))
                    return

            fileTargetPath = fileTargetPath.replace("\\", "/")
            if os.path.isdir(filepath):
                self.core.copyfolder(filepath, fileTargetPath)
            else:
                self.core.copyfile(filepath, fileTargetPath)

            logger.debug(f"Copied additional file: {file}")

        self.core.configs.clearCache(path=masterInfoPath)
        self.core.callback(name="masterVersionUpdated", args=[masterPath])
        return masterPath

    def _extractUsdMetadata(self, usdPath):
        """
        Extract metadata from a USD file (fps, metersPerUnit, upAxis, etc.)
        Returns a dict with metadata values, or defaults if file can't be read.
        """
        metadata = {
            "framesPerSecond": 24,
            "metersPerUnit": 1,
            "timeCodesPerSecond": 24,
            "upAxis": "Y"
        }

        try:
            # Try to read basic metadata from the file
            with open(usdPath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(2000)  # Read first 2000 chars to find metadata

                # Simple parsing for common metadata (works for ASCII .usda files)
                if "framesPerSecond" in content:
                    import re
                    match = re.search(r'framesPerSecond\s*=\s*(\d+(?:\.\d+)?)', content)
                    if match:
                        metadata["framesPerSecond"] = float(match.group(1))

                if "metersPerUnit" in content:
                    import re
                    match = re.search(r'metersPerUnit\s*=\s*(\d+(?:\.\d+)?)', content)
                    if match:
                        metadata["metersPerUnit"] = float(match.group(1))

                if "timeCodesPerSecond" in content:
                    import re
                    match = re.search(r'timeCodesPerSecond\s*=\s*(\d+(?:\.\d+)?)', content)
                    if match:
                        metadata["timeCodesPerSecond"] = float(match.group(1))

                if "upAxis" in content:
                    import re
                    match = re.search(r'upAxis\s*=\s*"([YZ])"', content)
                    if match:
                        metadata["upAxis"] = match.group(1)

        except Exception as e:
            logger.warning(f"Could not extract USD metadata from {usdPath}: {e}")

        return metadata

    def _generateUsdReferenceFile(self, relPath, defaultPrim, metadata, sourceVersion):
        """
        Generate USD reference file content.

        Args:
            relPath: Relative path to the versioned USD file
            defaultPrim: Name of the default prim
            metadata: Dict with fps, metersPerUnit, upAxis, etc.
            sourceVersion: The source version number (e.g., "v0024")

        Returns:
            String containing the USD ASCII file content
        """
        fps = metadata.get("framesPerSecond", 24)
        metersPerUnit = metadata.get("metersPerUnit", 1)
        timeCodesPerSecond = metadata.get("timeCodesPerSecond", 24)
        upAxis = metadata.get("upAxis", "Y")

        usdContent = f'''#usda 1.0
(
    defaultPrim = "{defaultPrim}"
    doc = """Generated by Prism Pipeline - MH Extension"""
    framesPerSecond = {fps}
    metersPerUnit = {metersPerUnit}
    timeCodesPerSecond = {timeCodesPerSecond}
    upAxis = "{upAxis}"
)

def "{defaultPrim}" (
    prepend references = @{relPath}@
)
{{
}}
'''
        return usdContent
