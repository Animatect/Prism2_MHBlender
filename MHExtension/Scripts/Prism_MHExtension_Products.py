# -*- coding: utf-8 -*-
#
# MH Extension - Product Management
# Handles product browser customization and ASSET grouping logic
#

import os
import inspect
import logging

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
