# Prism Master Versions - Technical Reference

This document explains how Prism's master version system works for products/renders.

## Overview

Master versions are special "pointer" versions that always reference the latest approved version of a product. Instead of hardcoding "v0001" or "v0023" in downstream files, you reference "master" which automatically points to the current production version.

## Core Files

- **[Products.py](C:\Program Files\Prism2\Scripts\PrismUtils\Products.py)** - Core master version logic
- **[ProductBrowser.py](C:\Program Files\Prism2\Scripts\ProjectScripts\ProductBrowser.py)** - UI for browsing and setting masters
- **[default_Export.py](C:\Program Files\Prism2\Scripts\ProjectScripts\StateManagerNodes\default_Export.py)** - Auto-creates masters on export

## How Master Versions Are Created

### Method 1: Manual (Product Browser)

**User Action:**
1. Open Product Browser (Assets/Shots → Products tab)
2. Right-click on any version
3. Select "Set as master"

**Code Flow:**
- [ProductBrowser.py:624-629](C:\Program Files\Prism2\Scripts\ProjectScripts\ProductBrowser.py#L624-L629) - Context menu
- Calls `core.products.updateMasterVersion(path)`
- [Products.py:734-855](C:\Program Files\Prism2\Scripts\PrismUtils\Products.py#L734-L855) - Main implementation

### Method 2: Automatic (Export State)

**User Action:**
1. In State Manager, create/edit an Export state
2. Check "Update Master Version" checkbox
3. Execute the state (publish/export)

**Code Flow:**
- [default_Export.py:163-164](C:\Program Files\Prism2\Scripts\ProjectScripts\StateManagerNodes\default_Export.py#L163-L164) - Checkbox loading
- [default_Export.py:946-952](C:\Program Files\Prism2\Scripts\ProjectScripts\StateManagerNodes\default_Export.py#L946-L952) - Check if should update
- [default_Export.py:955-959](C:\Program Files\Prism2\Scripts\ProjectScripts\StateManagerNodes\default_Export.py#L955-L959) - `handleMasterVersion()` wrapper
- [default_Export.py:1212-1213](C:\Program Files\Prism2\Scripts\ProjectScripts\StateManagerNodes\default_Export.py#L1212-L1213) - Called after successful export
- Calls `core.products.updateMasterVersion(outputName)`

## Master Version Creation Process

Function: `updateMasterVersion()` in [Products.py:734-855](C:\Program Files\Prism2\Scripts\PrismUtils\Products.py#L734-L855)

### Steps:

1. **Extract Source Data** (lines 735-748)
   - Get product/entity data from source version path
   - Determine location (global/local) - can override with `PRISM_PRODUCT_MASTER_LOC` env var
   - Validate source version exists

2. **Generate Master Path** (lines 750-763)
   - Use `generateProductPath()` with `version="master"`
   - Creates path like: `.../{product}/master/{files}`

3. **Delete Existing Master** (lines 765-768)
   - Calls `deleteMasterVersion()` to remove old master
   - Shows error dialog if deletion fails
   - Optionally renames old master to `.delete` folder

4. **Copy/Link Files** (lines 780-805)
   - **Hardlinks** (Windows, same drive):
     - If env var `PRISM_USE_HARDLINK_MASTER` is set
     - Uses `self.core.createSymlink(masterPathPadded, seqFile)`
   - **Copy** (default):
     - Uses `shutil.copy2(seqFile, masterPathPadded)`
   - Handles file sequences (detects and processes all frames)

5. **Copy Version Info** (lines 806-826)
   - Copies/links `versioninfo.yml` (or `.json`)
   - Updates `preferredFile` if needed
   - Stores original version number in master's metadata

6. **Copy Additional Files** (lines 828-851)
   - Copies all other files/folders from source version
   - For ShotCam: renames files replacing version with "master"
   - Uses `core.copyfolder()` for directories

7. **Cleanup & Callback** (lines 853-855)
   - Clears config cache
   - Fires `masterVersionUpdated` callback

## Master Version Display

### UI Representation

- **Version List**: Masters appear as "master" or "master (v0001)"
- **Sorting**: Masters always sort to top ([ProductBrowser.py:1589-1596](C:\Program Files\Prism2\Scripts\ProjectScripts\ProductBrowser.py#L1589-L1596))
- **Label Function**: `getMasterVersionLabel()` in [Products.py:942-950](C:\Program Files\Prism2\Scripts\PrismUtils\Products.py#L942-L950)

### Version Info Storage

Master versions store metadata about their source:
- `sourceVersion` - Original version number (e.g., "v0023")
- `version` - Also stored as fallback
- Retrieved via `getMasterVersionNumber()` in [Products.py:933-939](C:\Program Files\Prism2\Scripts\PrismUtils\Products.py#L933-L939)

## Master Version Deletion

**User Action:**
- Right-click master version → "Delete master"

**Code:**
- [ProductBrowser.py:617-622](C:\Program Files\Prism2\Scripts\ProjectScripts\ProductBrowser.py#L617-L622) - UI trigger
- [Products.py:894-930](C:\Program Files\Prism2\Scripts\PrismUtils\Products.py#L894-L930) - `deleteMasterVersion()`

**Fallback Strategies:**
1. Try `shutil.rmtree(masterFolder)`
2. If locked, clear UI selection and retry
3. If still locked, rename to `.delete/master_1`, `.delete/master_2`, etc.
4. Show retry/cancel dialog if all fail

## Configuration Settings

### Project-Wide Setting
```python
self.core.products.getUseMaster()  # Returns True/False
```
- Location: [Products.py:1076-1079](C:\Program Files\Prism2\Scripts\PrismUtils\Products.py#L1076-L1079)
- Config path: `globals → useMasterVersion` in project config
- Default: `True`

### Export State Setting
```python
self.chb_master.isChecked()  # User checkbox
```
- Saved in scene state data as `updateMasterVersion`
- Only used if project-wide setting is also enabled

### UI Visibility
```python
if not self.core.products.getUseMaster():
    self.w_master.setVisible(False)  # Hide checkbox
```
- [default_Export.py:617-618](C:\Program Files\Prism2\Scripts\ProjectScripts\StateManagerNodes\default_Export.py#L617-L618)

## Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `PRISM_PRODUCT_MASTER_LOC` | Force master location (global/local) | Location from source path |
| `PRISM_USE_HARDLINK_MASTER` | Use hardlinks instead of copy (Windows) | Not set (uses copy) |

## Special Cases

### Renderfarm Submission

When exporting to renderfarm ([default_Export.py:1176-1180](C:\Program Files\Prism2\Scripts\ProjectScripts\StateManagerNodes\default_Export.py#L1176-L1180)):
```python
handleMaster = "product" if self.isUsingMasterVersion() else False
plugin.sm_render_submitJob(self, outputName, parent, handleMaster=handleMaster, details=details)
updateMaster = False  # Renderfarm handles master creation
```

The renderfarm plugin decides when/how to create the master (typically after all frames complete).

### ShotCam Exports

Camera exports have dedicated master handling ([default_Export.py:1066-1068](C:\Program Files\Prism2\Scripts\ProjectScripts\StateManagerNodes\default_Export.py#L1066-L1068)):
- Always uses `_ShotCam` as product name
- Files renamed from `{version}` to `master` in filename
- Metadata updated to reflect shot context

## Version Retrieval

### Get Latest Version (including master)
```python
version = self.core.products.getLatestVersionFromProduct(
    product="myProduct",
    entity=entityData,
    includeMaster=True  # Will return master if it exists
)
```
- [Products.py:432-446](C:\Program Files\Prism2\Scripts\PrismUtils\Products.py#L432-L446)

### Get Latest Numbered Version (exclude master)
```python
version = self.core.products.getLatestVersionFromProduct(
    product="myProduct",
    entity=entityData,
    includeMaster=False  # Skips master, returns highest v#### version
)
```

## Callbacks

### On Master Update
```python
self.core.callback(name="masterVersionUpdated", args=[masterPath])
```
- Fired at [Products.py:854](C:\Program Files\Prism2\Scripts\PrismUtils\Products.py#L854)
- Use for custom post-master-creation logic

## Common Integration Points

### Custom Export State (like MH Blender Extension)

To support master versions in custom export states:

1. **Add UI Checkbox**
   ```python
   self.chb_master = QCheckBox("Update Master Version")
   ```

2. **Check Project Setting**
   ```python
   if not self.core.products.getUseMaster():
       self.chb_master.setVisible(False)
   ```

3. **After Export, Call Update**
   ```python
   if self.chb_master.isChecked() and self.core.products.getUseMaster():
       self.core.products.updateMasterVersion(exportedFilePath)
   ```

4. **Save State**
   ```python
   stateProps["updateMasterVersion"] = self.chb_master.isChecked()
   ```

## File Structure Example

```
Products/
└── myAsset/
    └── myProduct/
        ├── v0001/
        │   ├── myAsset_myProduct_v0001.abc
        │   └── versioninfo.yml
        ├── v0002/
        │   ├── myAsset_myProduct_v0002.abc
        │   └── versioninfo.yml
        ├── v0003/
        │   ├── myAsset_myProduct_v0003.abc
        │   └── versioninfo.yml
        └── master/  ← Points to v0003 (copies/links files)
            ├── myAsset_myProduct_master.abc  (copy/link of v0003)
            └── versioninfo.yml  (contains sourceVersion: "v0003")
```

## Troubleshooting

### Master Won't Delete
- File is locked by another process
- Prism tries renaming to `.delete` folder
- Manually close applications using the files
- Check `.delete` folder for old masters

### Master Not Updating Automatically
1. Check project setting: `getUseMaster()` returns `True`
2. Check export state: "Update Master Version" is checked
3. Verify export completed successfully (master updates after export)
4. Check logs for errors during `updateMasterVersion()`

### Hardlinks vs Copies
- **Hardlinks**: Instant, no extra disk space, same drive only (Windows)
- **Copies**: Works cross-drive, uses disk space, safer for modification
- Set `PRISM_USE_HARDLINK_MASTER` env var to enable hardlinks
- Only works on Windows, same drive, non-UNC paths

## MH Extension: USD Master Versions

The MH Extension adds special handling for USD files (.usda, .usdc, .usd) when creating master versions.

### USD Reference-Based Masters

**Location**: [Prism_MHExtension_Products.py:173-425](MHExtension/Scripts/Prism_MHExtension_Products.py#L173-L425)

Instead of copying USD files, the extension creates a lightweight reference file:

```python
# Monkey patched in Prism_MHExtension_Functions.py line 86-93
self.core.plugins.monkeyPatch(
    self.core.products.updateMasterVersion,
    self.productsManager.updateMasterVersion,
    self,
    force=True
)
```

### Behavior

**For USD files (.usda, .usdc, .usd):**
1. Creates a master `.usda` file that references the versioned file
2. Master file uses relative paths: `@../v0024/file_v0024.usdc@`
3. Extracts and preserves USD metadata (fps, upAxis, metersPerUnit)
4. Copies version info and non-USD files normally
5. Skips copying actual USD files (saves disk space)

**For all other file types:**
- Falls back to standard Prism behavior (copy or hardlink)

### USD Master File Format

```usda
#usda 1.0
(
    defaultPrim = "configure_geo_layer"
    doc = """Generated by Prism Pipeline - MH Extension"""
    framesPerSecond = 24
    metersPerUnit = 1
    timeCodesPerSecond = 24
    upAxis = "Y"
)

def "configure_geo_layer" (
    prepend references = @../v0024/chartoOmit_usdlayer_geo_v0024.usdc@
)
{
}
```

### Default Prim Naming

- **usdlayer_* products**: `configure_{layertype}_layer`
  - Example: `usdlayer_geo` → `configure_geo_layer`
- **Regular products**: Uses entity name (asset or shot name)

### Implementation Details

**Key Functions:**
- `updateMasterVersion()` - Main monkey-patched function
- `_extractUsdMetadata()` - Parses USD metadata from source file
- `_generateUsdReferenceFile()` - Creates USD ASCII reference content

**Metadata Extraction:**
- Reads first 2000 characters of source USD file
- Uses regex to extract: fps, metersPerUnit, timeCodesPerSecond, upAxis
- Falls back to defaults if parsing fails (24 fps, 1m unit, Y-up)

**Benefits:**
- ✅ Saves disk space (references instead of copies)
- ✅ Updates propagate automatically (master always references latest)
- ✅ Works with any USD-aware application
- ✅ Preserves metadata from source files
- ✅ Compatible with USD composition arcs

## Related Documentation

See [CLAUDE.md](CLAUDE.md) for MH Blender Extension architecture and integration points.
