# Settings Added - USD Master Version Control

## Summary

Added a user-configurable setting to control whether USD files use reference-based master versions or standard copy/hardlink behavior.

## Changes Made

### 1. Settings UI ([Prism_MHExtension_Integration.py](MHExtension/Scripts/Prism_MHExtension_Integration.py))

**Added USD Master Version Settings Group Box (lines 184-211):**
- New section in MH Prism Extension settings tab
- Checkbox: "Use referenced files as master on USD files"
- Default state: Checked (enabled)
- Tooltip with detailed explanation of behavior
- Info label explaining the feature

**Added Save/Load Settings (lines 628, 644-648, 654-674):**
- `userSettings_saveSettings()`: Saves checkbox state to config
- `userSettings_loadSettings()`: Loads checkbox state from config (defaults to True if missing)
- `getUseUsdReferences()`: Getter method to retrieve setting value from UI or config

### 2. Updated Master Version Logic ([Prism_MHExtension_Products.py](MHExtension/Scripts/Prism_MHExtension_Products.py))

**Modified `updateMasterVersion()` (lines 197-206):**
```python
# Check user setting for USD reference behavior
useUsdReferences = self.plugin.getUseUsdReferences() if hasattr(self.plugin, 'getUseUsdReferences') else True

if not isUsdFile or not useUsdReferences:
    # Not a USD file OR user disabled USD reference mode - use original behavior
    reason = f"Non-USD file {ext}" if not isUsdFile else f"USD references disabled in settings"
    logger.debug(f"{reason}, using original updateMasterVersion")
    return self.core.plugins.callUnpatchedFunction(
        self.core.products.updateMasterVersion, path
    )
```

**Behavior:**
- If setting is **enabled** (default): USD files use reference-based masters
- If setting is **disabled**: USD files use standard Prism copy/hardlink behavior
- Non-USD files always use standard behavior regardless of setting

### 3. Updated Documentation

**[USD_MASTER_VERSION_IMPLEMENTATION.md](USD_MASTER_VERSION_IMPLEMENTATION.md):**
- Added "Configuration" section explaining the new setting
- Added "How to Enable/Disable" instructions
- Updated testing section with steps to test both modes

**[PRISM_MASTER_VERSIONS.md](PRISM_MASTER_VERSIONS.md):**
- Updated behavior section to mention the setting
- Added configuration details
- Added to benefits list

## User Interface

### Settings Location

**Path**: Prism Settings → MH Prism Extension → USD Master Version Settings

**Screenshot Structure**:
```
┌─ MH Prism Extension Tab ─────────────────────┐
│                                               │
│ ┌─ Fusion Configuration ──────────────────┐  │
│ │ ...                                      │  │
│ └──────────────────────────────────────────┘  │
│                                               │
│ ┌─ Presets Configuration ─────────────────┐  │
│ │ ...                                      │  │
│ └──────────────────────────────────────────┘  │
│                                               │
│ ┌─ Blender Configuration ─────────────────┐  │
│ │ ...                                      │  │
│ └──────────────────────────────────────────┘  │
│                                               │
│ ┌─ USD Master Version Settings ───────────┐  │
│ │ ☑ Use referenced files as master on     │  │
│ │   USD files                              │  │
│ │                                          │  │
│ │ Note: When using references, master     │  │
│ │ files will be small .usda files that    │  │
│ │ reference the versioned file.           │  │
│ │ This is the recommended setting for     │  │
│ │ USD workflows.                           │  │
│ └──────────────────────────────────────────┘  │
│                                               │
└───────────────────────────────────────────────┘
```

## Configuration Data

**Storage Location**: Prism user settings config file

**Config Structure**:
```python
{
    "MHExtension": {
        "FusionDir": "...",
        "BlenderDir": "...",
        "useUsdReferences": True  # ← New setting
    }
}
```

## Default Behavior

- **Default value**: `True` (enabled)
- **Fallback behavior**: If setting doesn't exist or can't be read, defaults to `True`
- **Applies to**: Only affects USD files (.usda, .usdc, .usd)
- **Scope**: Setting applies to all future master version operations

## Testing Checklist

- [x] UI checkbox appears in settings
- [x] Checkbox state saves to config
- [x] Checkbox state loads from config
- [x] Setting defaults to True when missing
- [x] Enabled: USD masters use references
- [x] Disabled: USD masters use copy/hardlink
- [x] Non-USD files unaffected by setting
- [x] Documentation updated

## Implementation Notes

1. **Backward Compatible**: Existing installations without this setting will default to enabled (reference mode)
2. **Per-User**: Setting is stored in user config, not project config
3. **Dynamic**: Can be changed at any time; affects only future master versions
4. **Safe Fallback**: If setting can't be read, defaults to enabled (recommended behavior)
5. **Graceful Degradation**: If `getUseUsdReferences()` method doesn't exist, defaults to `True`

## Code References

| Component | File | Lines | Description |
|-----------|------|-------|-------------|
| UI Group Box | Prism_MHExtension_Integration.py | 184-211 | Settings UI section |
| Save Setting | Prism_MHExtension_Integration.py | 628 | Save checkbox to config |
| Load Setting | Prism_MHExtension_Integration.py | 644-648 | Load checkbox from config |
| Getter Method | Prism_MHExtension_Integration.py | 654-674 | Retrieve setting value |
| Use Setting | Prism_MHExtension_Products.py | 197-206 | Check and apply setting |
