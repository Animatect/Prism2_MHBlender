# USD Export Extension for Prism Pipeline

This plugin extends Prism Pipeline's default Export state to support USD (Universal Scene Description) file export in Blender.

## Features

- **USD Format Support**: Export to `.usd`, `.usda` (ASCII), or `.usdc` (binary) formats
- **Comprehensive Export Options**:
  - Materials and shader networks
  - UV coordinate maps
  - Mesh normals
  - Animation data
  - Hair/Curves
  - Instancing optimization
  - Viewport or Render evaluation modes
- **Seamless Integration**: Works with Prism's existing Export state workflow
- **Settings Persistence**: All USD settings are saved with your Prism scene state

## Installation

### Method 1: Via Prism Settings (Recommended)

1. Open Prism Settings (Prism Tray > Settings or from within your DCC app)
2. Navigate to the **Plugins** tab
3. Click **Add** and browse to `Prism_USDExport_Extension.py`
4. Click **OK** to load the plugin
5. Restart your DCC application

### Method 2: Manual Installation

1. Copy `Prism_USDExport_Extension.py` to your Prism plugins directory:
   - **Project Plugins**: `[ProjectRoot]/00_Pipeline/Plugins/Custom/`
   - **User Plugins**: `[PrismConfig]/Plugins/Custom/`

2. Restart Prism or reload plugins from Prism Settings

## Usage

### Basic Workflow

1. **Open State Manager** in Blender (via Prism menu)
2. **Create an Export State** (right-click > Export)
3. **Select USD as Output Type**:
   - In the Export state, find the "Output Type" dropdown
   - Select `.usd`, `.usda`, or `.usdc`
4. **Configure USD Settings**:
   - The "USD Export Settings" section will appear automatically
   - Adjust options as needed (materials, UVs, animation, etc.)
5. **Add Objects** to export (or check "Whole Scene")
6. **Set Frame Range** if exporting animation
7. **Execute** the state to export

### USD Export Settings Explained

#### USD Format
- **Binary (usdc)**: Compact binary format, faster to load/save, smaller file size
- **ASCII (usda)**: Human-readable text format, easier to inspect and version control

#### Export Materials
Export material assignments and shader networks. Enable this to preserve your materials in the USD file.

#### Export UV Maps
Export UV coordinate data for texturing. Required if you want to apply textures downstream.

#### Export Normals
Export mesh normal data. Important for smooth shading and rendering.

#### Export Animation
Export animated transforms and deformations. When enabled, respects the frame range settings.

#### Export Hair/Curves
Export hair particle systems and curves as USD curves. Useful for hair, fur, and procedural elements.

#### Use Instancing
Export instances where possible for better performance. Recommended for scenes with many duplicated objects.

#### Evaluation Mode
- **Viewport**: Use viewport display settings (faster, lighter geometry)
- **Render**: Use render settings with modifiers and subdivision applied (slower, final quality)

## Examples

### Export Static Model
```
1. Output Type: .usdc
2. USD Format: Binary (usdc)
3. Frame Range: Single Frame
4. Export Materials: ✓
5. Export UVs: ✓
6. Export Normals: ✓
7. Export Animation: ✗
8. Evaluation Mode: Render
```

### Export Animated Character
```
1. Output Type: .usd
2. USD Format: Binary (usdc)
3. Frame Range: Shot (or Custom)
4. Export Materials: ✓
5. Export UVs: ✓
6. Export Normals: ✓
7. Export Animation: ✓
8. Export Hair/Curves: ✓ (if character has hair)
9. Evaluation Mode: Render
```

### Export for Version Control (ASCII)
```
1. Output Type: .usda
2. USD Format: ASCII (usda)
3. Frame Range: Single Frame
4. Export Materials: ✓
5. Export UVs: ✓
6. Export Normals: ✓
7. Evaluation Mode: Viewport
```

## Technical Details

### How It Works

The plugin uses Prism's callback system to:

1. **Add USD formats** (`.usd`, `.usda`, `.usdc`) to Blender's available export formats
2. **Inject UI elements** into the Export state to configure USD-specific settings
3. **Monkey-patch** the Blender app plugin's export function to intercept USD exports
4. **Call Blender's native USD exporter** (`bpy.ops.wm.usd_export`) with configured parameters

### Callback Registration

The plugin registers these callbacks:

- `onPluginLoaded`: Adds USD formats and patches export function
- `onStateStartup`: Adds USD settings UI to Export states
- `onStateGetSettings`: Saves USD settings to scene
- `onStateSettingsLoaded`: Loads USD settings from scene
- `preExport`: Pre-export logging and validation
- `postExport`: Post-export logging and cleanup

### Settings Storage

All USD settings are saved in the Prism scene state data under these keys:
- `usd_format`
- `usd_materials`
- `usd_uvmaps`
- `usd_normals`
- `usd_animation`
- `usd_hair`
- `usd_instancing`
- `usd_eval_mode`

## Requirements

- **Prism Pipeline**: v2.0 or higher
- **Blender**: 2.82+ (with USD export support)
- **Python**: 3.9+ (bundled with Blender)

## Troubleshooting

### USD Settings Don't Appear

**Cause**: Plugin not loaded or Blender plugin not detected

**Solution**:
1. Check Prism Settings > Plugins to ensure the plugin is loaded
2. Restart Blender
3. Check the console for "[USD Export] Added USD formats" message

### Export Fails with "USD export failed"

**Cause**: Blender's USD library not available

**Solution**:
1. Ensure your Blender version supports USD (2.82+)
2. Check if Blender was compiled with USD support
3. Check the Blender console for detailed error messages

### Settings Not Saving

**Cause**: State Manager not saving properly

**Solution**:
1. Ensure you're using a valid Prism project
2. Try manually saving the scene state
3. Check file permissions on your project directory

## Extending the Plugin

You can modify the plugin to add more USD export options:

1. **Add New UI Element** in `onStateStartup()`
2. **Save Setting** in `onStateGetSettings()`
3. **Load Setting** in `onStateSettingsLoaded()`
4. **Use Setting** in `exportUSD()` when calling `bpy.ops.wm.usd_export()`

Example - Adding subdivision level control:

```python
# In onStateStartup():
state.w_usdSubdivision = QWidget()
state.lo_usdSubdivision = QHBoxLayout(state.w_usdSubdivision)
state.l_usdSubdivision = QLabel("Subdivision Level:")
state.sb_usdSubdivision = QSpinBox()
state.sb_usdSubdivision.setRange(0, 6)
state.lo_usdSubdivision.addWidget(state.l_usdSubdivision)
state.lo_usdSubdivision.addWidget(state.sb_usdSubdivision)
state.lo_usd.addWidget(state.w_usdSubdivision)

# In exportUSD():
export_params['subdivision_level'] = origin.sb_usdSubdivision.value()
```

## License

This plugin follows the same license as your Prism2_MHBlender project.

## Support

For issues, feature requests, or questions:
- Check the Prism Pipeline documentation: https://prism-pipeline.com/docs/
- Review Blender's USD documentation: https://docs.blender.org/manual/en/latest/
- Consult this README for configuration help

## Version History

### v1.0.0 (Initial Release)
- USD format support (.usd, .usda, .usdc)
- Comprehensive export options
- Seamless Prism integration
- Settings persistence
