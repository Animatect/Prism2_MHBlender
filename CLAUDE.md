# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Prism2_MHBlender is a **Prism Pipeline plugin extension** that adds advanced Blender and Fusion functionality to the Prism Pipeline framework. This is NOT a standalone application - it's a plugin that extends the official Prism Blender and Fusion plugins.

**Key capabilities:**
- Advanced render layer creation and node management in Blender
- Layer enabling/disabling with automatic node muting
- Network rendering support
- Dedicated nodes for regular passes, technical passes (32-bit), and Cryptomattes
- Render output compatible with Fusion and Nuke
- Blender camera export format (.bcam) for BMD Fusion
- Fusion integration utilities (path maps, shot switcher, OCIO manager)
- Preset project templates with pipeline structure

**Requirements:**
- Python 3.9 or higher
- Prism Pipeline framework installed
- Blender with compositor nodes enabled
- Optional: BMD Fusion for integration features

## Architecture

### Plugin Structure

The plugin follows Prism's standard plugin architecture with separation of concerns:

```
MHExtension/
├── Scripts/                           # Core plugin logic
│   ├── Prism_MHExtension_init.py      # Main plugin entry point (combines Variables, Functions, Integration)
│   ├── Prism_MHExtension_Variables.py # Plugin metadata and configuration
│   ├── Prism_MHExtension_Functions.py # Cross-application plugin functions and callbacks
│   ├── Prism_BlenderMHExtension_Functions.py  # Blender-specific functionality
│   ├── Prism_FusionMHExtension_Functions.py   # Fusion-specific functionality
│   └── StateManagerNodes/             # Custom Prism state manager nodes
│       ├── bld_MHRender.py            # Main render state for Blender
│       ├── bld_MHrendLayer.py         # Render layer management state
│       ├── default_RenderSettings.py  # Render settings presets
│       └── StateUserInterfaces/       # Qt UI files and generated Python UI code
├── Integrations/
│   ├── Fusion/                        # Fusion scripts and configs
│   │   ├── MH_PrismShotSwitcher.py   # Shot switching utility for Fusion
│   │   ├── MH_PathMapsToAbsolute.py  # Convert Fusion path maps to absolute paths
│   │   ├── MH_AbsoluteToPathMaps.py  # Convert absolute paths to Fusion path maps
│   │   ├── BlenderOCIOmanager.py     # OCIO color management
│   │   └── MHMenu.fu                 # Fusion menu configuration
│   └── Presets/
│       └── Projects/
│           └── CGNOVADefault/         # Default project template structure
└── ...
```

### Key Architectural Patterns

1. **Multiple Inheritance Plugin Pattern**: The main plugin class (`Prism_MHExtension`) inherits from three base classes:
   - `Prism_MHExtension_Variables` - Configuration and metadata
   - `Prism_MHExtension_Functions` - Core plugin logic
   - `Prism_MHExtension_Integration` - Settings UI and integration management

2. **Application-Specific Function Classes**: The plugin dynamically loads application-specific functionality:
   - `Prism_BlenderMHExtension_Functions` - Loaded only when running in Blender
   - `Prism_FusionMHExtension_Functions` - Loaded only when running in Fusion
   - Detection via `self.core.appPlugin.appShortName.lower()` ("bld" or "fus")

3. **Monkey Patching**: The plugin uses Prism's monkey patching system to override or extend core functionality:
   - `self.core.plugins.monkeyPatch(target_method, replacement_method, self, force=True)`
   - Used for shotcam export, playblast, and version context handling

4. **Callback Registration**: Integrates with Prism's callback system:
   - `onUserSettings_loadUI` - Adds plugin settings tab
   - `onStateManagerOpen` - Registers custom state types
   - `onPluginLoaded` - Initializes app-specific functions
   - `onStateDeleted` - Cleanup when states are removed

5. **Custom State Manager Nodes**: Extends Prism's State Manager with custom render nodes that manage Blender view layers and compositor node trees.

## Blender-Specific Implementation

### MH Blender Panel

The plugin adds a custom "MH Ops" panel to Blender's Prism panel category:
- Located in `MHExtension/Integrations/Blender/MHBlenderInit.py`
- Installed via Prism Settings UI (similar to Fusion integration)
- Registers custom operators and UI panels in Blender
- Panel appears in the 3D Viewport sidebar (press `N`) under the "Prism" tab
- Loaded automatically as a Blender startup script

**Adding new operators to the MH Ops panel:**
1. Edit [MHBlenderInit.py](MHExtension/Integrations/Blender/MHBlenderInit.py)
2. Create a new Blender operator class inheriting from `bpy.types.Operator`
3. Define `bl_idname`, `bl_label`, and `execute()` method
4. Add the operator class to `register()` and `unregister()` functions
5. Add `layout.row().operator("object.your_operator_id")` in `MH_OpsPanel.draw()` to display the button
6. Reinstall via Prism Settings or manually copy the updated file to Blender's scripts/startup folder

### AOV (Arbitrary Output Variable) Management

The plugin maintains a mapping dictionary (`AOVDict`) that translates Blender's render pass names to shorter, production-friendly names:
- "ambient occlusion" → "AO"
- "cryptomatte object" → "CryptoObject"
- "diffuse color" → "DiffCol"
- etc.

### View Layer Properties

Managed via the `layerProperties` dictionary in `Prism_BlenderMHExtension_Functions.py`:
- Environment, Surfaces, Curves, Volumes
- Motion Blur, Denoising settings

### Render Engine Detection

The plugin checks which render engine is active:
- `isUsingCycles()` - Returns True if Cycles engine active
- `isUsingEevee()` - Returns True if Eevee engine active

## Fusion Integration

### Custom Import Handlers

The Fusion extension registers custom import handlers for:
- `.bcam` files (Blender camera format) via `importBlenderCam()`
- Imports camera data from Blender and creates Fusion camera nodes

### Path Map Utilities

Two complementary utilities for managing Fusion path maps:
- `MH_PathMapsToAbsolute.py` - Converts path map references to absolute paths
- `MH_AbsoluteToPathMaps.py` - Converts absolute paths to path map references
- Placeholders like `PRISMROOT` and `FUSIONROOT` are replaced during installation

### Shot Switcher

`MH_PrismShotSwitcher.py` provides a Qt-based UI for quickly switching between shots in a Fusion composition, with shot preview thumbnails.

## Installation System

The plugin includes a custom installation system managed via the Settings UI (Prism Settings > MH Prism Extension tab):

### Blender Integration Installation

Located in `Prism_MHExtension_Integration.py`:
- `addBlender(installPath)` - Installs MHBlenderInit.py to Blender's scripts/startup folder
- `removeBlender(installPath)` - Removes the integration file
- During installation, placeholder paths (PRISMROOT, MHEXTENSIONROOT) are replaced with actual paths
- Default Blender path: `%appdata%\Blender Foundation\Blender\4.5` (or your Blender version)
- The integration adds a "MH Ops" panel to Blender's Prism sidebar with custom operators

**Installation process:**
1. Open Prism Settings > MH Prism Extension tab
2. In the Blender Configuration section, click "Add"
3. Select your Blender version folder (e.g., `C:\Users\YourName\AppData\Roaming\Blender Foundation\Blender\4.5`)
4. The MHBlenderInit.py file will be copied to the `scripts/startup` folder
5. Restart Blender to see the "MH Ops" panel in the Prism tab

### Fusion Integration Installation

Located in `Prism_MHExtension_Integration.py`:
- `addFusion(installPath)` - Installs scripts to Fusion's Scripts/MH folder and configs to Config folder
- `removeFusion(installPath)` - Removes installed files
- During installation, placeholder paths (PRISMROOT, FUSIONROOT) are replaced with actual paths
- Default Fusion path: `%appdata%\Blackmagic Design\Fusion`

### Preset Projects Installation

- `addPresets()` - Copies preset project templates to Prism's user presets folder
- Includes the CGNOVADefault template with complete pipeline structure (Pipeline, Management, Designs, Production, Resources)
- Target: `{PrismUserConfig}/Presets/Projects/`

## Development Commands

### Testing in Blender
1. Open Blender
2. Install the Prism plugin if not already installed
3. Drag and drop `Prism_BlenderMHExtension.py` to Prism Settings > Plugins
4. Restart Prism
5. Enable "Use Nodes" in the Compositor before using render states

### Modifying Qt UI Files
- UI files are in `MHExtension/Scripts/StateManagerNodes/StateUserInterfaces/`
- After editing `.ui` files with Qt Designer, regenerate Python code using `ConvertUI.py`
- The UI conversion script converts `.ui` → `_ui.py` files

### Working with State Manager Nodes
- Custom states must be registered in `self.customstates` list
- State classes must define `className`, `listType`, and `stateCategories`
- UI files must match the state class name pattern (e.g., `bld_MHRender.ui` for `MHRenderClass`)

## Important Notes

- **Compositor Nodes Required**: Users must enable "Use Nodes" in Blender's compositor before using this plugin
- **Version Context Patching**: The plugin patches `getVersionStackContextFromPath` to customize version management behavior
- **Cross-Application Awareness**: Code must check `self.core.appPlugin.appShortName` before accessing app-specific APIs
- **Settings Persistence**: Settings are saved/loaded via `userSettings_saveSettings` and `userSettings_loadSettings` callbacks using Prism's config system
- **Error Handling**: All major functions use the `@err_catcher` decorator for consistent error reporting

## Common Integration Points

When extending this plugin:

1. **Adding New Fusion Scripts**: Add to `self.scripts` list in `Prism_MHExtension_Integration.__init__()`, then add installation logic in `addFusion()`

2. **Adding New State Manager Nodes**: Create state class in `StateManagerNodes/`, add UI file, add to `self.customstates` list, register via `stateTypeCreator()`

3. **Adding New AOV Types**: Update the `AOVDict` dictionary in `Prism_BlenderMHExtension_Functions.__init__()`

4. **Modifying Settings UI**: Edit `userSettings_loadUI()` to add UI elements, then implement save/load in `userSettings_saveSettings/loadSettings()`
