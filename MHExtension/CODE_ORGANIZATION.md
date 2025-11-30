# Code Organization

This document describes the organization of the MH Extension codebase and where to find specific functionality.

## Directory Structure

```
MHExtension/
├── Scripts/                                    # Core plugin logic
│   ├── Prism_MHExtension_Functions.py          # Main plugin functions and callbacks
│   ├── Prism_MHExtension_Products.py           # Product browser customization (NEW)
│   ├── Prism_BlenderMHExtension_Functions.py   # Blender-specific functionality
│   ├── Prism_FusionMHExtension_Functions.py    # Fusion-specific functionality
│   └── StateManagerNodes/                      # Custom Prism state manager nodes
└── Integrations/
    └── Blender/
        ├── MHBlenderInit.py                    # Blender panel and operators
        └── MHUsdExportState.py                 # USD export state UI (NEW)
```

## New Files and Their Purpose

### 1. `Prism_MHExtension_Products.py`
**Location:** `MHExtension/Scripts/`

**Purpose:** Centralized product management and browser customization

**Responsibilities:**
- Product browser monkey patching
- ASSET grouping logic
- `usdlayer_*` product grouping under ASSET
- Custom product icons
- Product display customization

**Key Methods:**
- `onProductBrowserOpen(productBrowser)` - Main entry point for product browser customization
- `getCustomProductIcon(productName)` - Returns custom icons for specific products
- `isGroupableProduct(productName)` - Determines if a product should be auto-grouped

**When to Edit:**
- Adding new product grouping rules
- Customizing product icons
- Modifying product browser behavior
- Adding ASSET-related functionality

---

### 2. `MHUsdExportState.py`
**Location:** `MHExtension/Integrations/Blender/`

**Purpose:** USD export state UI and settings management for Blender

**Responsibilities:**
- Creating USD-specific UI widgets for export states
- Managing USD export settings (format, object types, geometry, materials, instancing)
- Saving/loading USD export settings
- Showing/hiding USD settings based on selected format

**Key Methods:**
- `onStateStartup(state)` - Creates the USD settings UI when an export state is created
- `onStateGetSettings(state, settings)` - Collects settings for saving
- `onStateSettingsLoaded(state, settings)` - Loads saved settings
- `onOutputTypeChanged(state, outputType)` - Shows/hides USD settings

**Settings Managed:**
- **USD Format:** usd, usdc, usda (default: usd)
- **Object Types:** Meshes (ON), Lights (OFF), Cameras (OFF), Curves (ON), Point Clouds (OFF), Volumes (OFF)
- **Geometry:** Rename UV Maps (ON)
- **Materials:** Export Materials (OFF)
- **Instancing:** Export Instancing (OFF)

**When to Edit:**
- Adding new USD export options
- Changing default export settings
- Modifying USD export UI layout
- Adding new object type filters

---

## Integration with Main Plugin

### `Prism_MHExtension_Functions.py`

The main plugin file now delegates to these specialized modules:

```python
# Initialize modules
self.productsManager = Prism_MHExtension_Products(core, plugin)
self.usdExportState = MHUsdExportState.MHUsdExportState(self.core)

# Register callbacks
self.core.registerCallback("onProductBrowserOpen",
                          self.productsManager.onProductBrowserOpen,
                          plugin=self.plugin)

# Delegate callbacks
def onStateStartup(self, state):
    if self.usdExportState:
        self.usdExportState.onStateStartup(state)
```

## Best Practices

### When Adding Product-Related Features
1. Edit `Prism_MHExtension_Products.py`
2. Add methods to the `Prism_MHExtension_Products` class
3. Update `onProductBrowserOpen()` if needed
4. Test with various product types (ASSET, usdlayer_*, etc.)

### When Adding USD Export Features
1. Edit `MHUsdExportState.py`
2. Add UI widgets in `onStateStartup()`
3. Add settings saving in `onStateGetSettings()`
4. Add settings loading in `onStateSettingsLoaded()`
5. Update default values as needed

### When Adding General Plugin Features
1. Edit `Prism_MHExtension_Functions.py` for cross-application logic
2. Edit `Prism_BlenderMHExtension_Functions.py` for Blender-specific logic
3. Edit `Prism_FusionMHExtension_Functions.py` for Fusion-specific logic

## Migration Notes

The following functionality has been **moved** from `Prism_MHExtension_Functions.py`:

### To `Prism_MHExtension_Products.py`:
- ✅ `onProductBrowserOpen()` - Product browser customization
- ✅ ASSET grouping logic
- ✅ `usdlayer_*` grouping logic
- ✅ Custom icon handling for ASSET

### To `MHUsdExportState.py`:
- ✅ `onStateStartup()` - USD settings UI creation
- ✅ `onStateGetSettings()` - USD settings saving
- ✅ `onStateSettingsLoaded()` - USD settings loading
- ✅ `onOutputTypeChanged()` - Show/hide USD settings
- ✅ All USD export UI widget creation code

The main functions file now only contains:
- Core plugin initialization
- Callback registration
- Delegation to specialized modules
- State manager integration
- General utility functions

## Benefits of This Organization

1. **Separation of Concerns:** Each file has a clear, focused purpose
2. **Easier Maintenance:** Related code is grouped together
3. **Better Scalability:** Easy to add new product types or export formats
4. **Cleaner Code:** Reduced complexity in main plugin file
5. **Modular Testing:** Can test products and USD export independently
6. **Clear Documentation:** Easy to find where specific features are implemented
