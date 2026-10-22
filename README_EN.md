# c4d-jimeng-uploader

[中文说明](README.md)

Cinema 4D white-model uploader for Jimeng, for C4D 2026.3.1. This plug-in uses Cinema 4D's native **Viewport Renderer** to output white-model animation as MP4, then passes it to the Jimeng web app through a temporary local bridge.

Repository: [Aitidi/c4d-jimeng-uploader](https://github.com/Aitidi/c4d-jimeng-uploader). The project name, plug-in menu, window title, and installation folder all use `c4d-jimeng-uploader`. The Python entry point is `c4d_jimeng_uploader.pyp`, and the module directory is `c4d_jimeng_uploader`.

## Installation

1. Download and extract the installation archive from [Releases](https://github.com/Aitidi/c4d-jimeng-uploader/releases/latest). Copy the complete `c4d-jimeng-uploader` folder, including its `presets` subfolder, into the Cinema 4D 2026 `plugins` directory. If using a source ZIP, rename the extracted project root to `c4d-jimeng-uploader` first.
2. Restart Cinema 4D.
3. Open **c4d-jimeng-uploader** from the Extensions menu.
4. On first launch, the plug-in imports the built-in `Jimeng Viewport White Model` Render Settings preset into the current `.c4d` file.

When upgrading, remove any previous `jimeng_c4d_uploader` or `jimeng-c4d-uploader` installation folder from `plugins` to avoid loading duplicate copies. Existing preferences are still read from `JimengC4DUploader/settings.json` and written to `%APPDATA%/c4d-jimeng-uploader/settings.json` on the next save. The built-in render preset retains its name, `Jimeng Viewport White Model`, for compatibility with existing scenes.

## Usage

1. Select a camera. `Jimeng Viewport White Model` is the only Render Settings preset used by the plug-in. Frame range, frame rate, and Save path are read from that preset. When rendering starts from another active Render Settings entry, only its output width and height are copied to the Jimeng preset.
2. Select **Render Settings** to make the Jimeng preset active and open Cinema 4D's native **Edit Render Settings** window. Adjust Output, Save, and Viewport Renderer options there.
3. Select **Reset Render Settings** to restore the complete built-in Asset Browser preset, including its Save path and filename tokens. This does not add material overrides, effects, or other render modules.
4. Select **Render & Upload**. If the current `.c4d` file has not been saved, the plug-in opens Cinema 4D's native Save dialog first. It then switches temporarily to the Jimeng preset and runs C4D's native **Render to Picture Viewer** command, not Alt+B / Make Preview. After C4D writes the MP4, the previous Render Settings and camera are restored before upload.
5. Select **Open Link**. The generated link uses a temporary local HTTP service: it expires after 30 minutes and closes 60 seconds after the web page starts downloading the file.

## Dependencies and limitations

- Viewport Renderer only supports local rendering and cannot use Team Render.
- The Jimeng web protocol and localhost cross-origin behavior are not public APIs. The bridge may need updates if the web app changes.
- Set `C4D_JIMENG_UPLOADER_FFMPEG` to an FFmpeg executable for full codec checks; the legacy `JIMENG_UPLOADER_FFMPEG` variable is also supported. Without FFmpeg, only the container and H.264 markers are checked.

## Development and packaging

- Run `python -m unittest discover -s tests -v` to execute tests.
- Run `./build_release.ps1` to create `dist/c4d-jimeng-uploader-v<version>.zip`. The archive name and installation folder are independent of the source folder name.
