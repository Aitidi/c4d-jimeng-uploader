# Jimeng Seedance White Model Uploader (C4D 2026.3.1)

[中文说明](README.md)

This plug-in uses Cinema 4D's native **Viewport Renderer** to output white-model animation as MP4, then passes it to the Jimeng web app through a temporary local bridge.

## Installation

1. Copy the complete `jimeng_c4d_uploader` folder, including its `presets` subfolder, into the Cinema 4D 2026 `plugins` directory.
2. Restart Cinema 4D.
3. Open **Seedance_c4d_uploader** from the Extensions menu.
4. On first launch, the plug-in imports the built-in `Jimeng Viewport White Model` Render Settings preset into the current `.c4d` file.

## Usage

1. Select a camera. `Jimeng Viewport White Model` is the only Render Settings preset used by the plug-in. Frame range, frame rate, and Save path are read from that preset. When rendering starts from another active Render Settings entry, only its output width and height are copied to the Jimeng preset.
2. Select **Render Settings** to make the Jimeng preset active and open Cinema 4D's native **Edit Render Settings** window. Adjust Output, Save, and Viewport Renderer options there.
3. Select **Reset Render Settings** to restore the complete built-in Asset Browser preset, including its Save path and filename tokens. This does not add material overrides, effects, or other render modules.
4. Select **Render & Upload**. If the current `.c4d` file has not been saved, the plug-in opens Cinema 4D's native Save dialog first. It then switches temporarily to the Jimeng preset and runs C4D's native **Render to Picture Viewer** command, not Alt+B / Make Preview. After C4D writes the MP4, the previous Render Settings and camera are restored before upload.
5. Select **Open Link**. The generated link uses a temporary local HTTP service: it expires after 30 minutes and closes 60 seconds after the web page starts downloading the file.

## Dependencies and limitations

- Viewport Renderer only supports local rendering and cannot use Team Render.
- The Jimeng web protocol and localhost cross-origin behavior are not public APIs. The bridge may need updates if the web app changes.
