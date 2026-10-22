"""Stable identifiers and UI labels for the Cinema 4D plug-in."""

import os

# This is a development ID. Obtain a unique Plugin Café ID before distributing
# the plug-in outside this workstation.
PLUGIN_ID = 1069872
PLUGIN_NAME = "c4d-jimeng-uploader"
PLUGIN_HELP = "Render Viewport Renderer white-model MP4 videos and upload them to Jimeng / 使用 Viewport Renderer 渲染白模 MP4 并上传至即梦"

WHITE_RENDER_SETTINGS_NAME = "Jimeng Viewport White Model"
# This asset database ships with the plug-in. Do not use a user-specific
# Documents path: an entire plug-in folder can be copied to a new workstation.
PLUGIN_DIRECTORY = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
RENDER_SETTINGS_PRESET_DIRECTORY = os.path.join(PLUGIN_DIRECTORY, "presets", WHITE_RENDER_SETTINGS_NAME)
# Stored in the scene-local RenderData so a changed Asset Browser preset is
# imported once without overwriting the user's unchanged preset every launch.
PRESET_VERSION_CONTAINER_ID = 106987201

# C4D core command: Render > Render to Picture Viewer (Shift+R).
RENDER_TO_PICTURE_VIEWER_COMMAND = 12099
# C4D core command: File > Save Project (Ctrl+S).
SAVE_DOCUMENT_COMMAND = 12098

MODE_CAMERA = 0
MODE_LOCAL = 1

# GeDialog gadget IDs.
ID_MODE = 1000
ID_CAMERA = 1001
ID_RENDER_SETTINGS = 1002
ID_FRAME_START = 1004
ID_FRAME_END = 1005
ID_OUTPUT_DIR = 1006
ID_LOCAL_VIDEO = 1008
ID_STATUS = 1009
ID_LINK = 1010

ID_REFRESH = 1100
ID_LANGUAGE = 1101
ID_BROWSE_VIDEO = 1102
ID_NATIVE_RENDER_SETTINGS = 1103
ID_APPLY_WHITE_PRESET = 1104
ID_RENDER_UPLOAD = 1105
ID_UPLOAD_LOCAL = 1106
ID_PREVIEW = 1107
ID_OPEN_LINK = 1108
ID_COPY_LINK = 1109

# Static text gadget IDs.
ID_LABEL_MODE = 2001
ID_LABEL_CAMERA = 2002
ID_LABEL_RENDER_SETTINGS = 2003
ID_LABEL_FRAME_START = 2005
ID_LABEL_FRAME_END = 2006
ID_LABEL_OUTPUT_DIR = 2007
ID_LABEL_LOCAL_VIDEO = 2010
ID_LABEL_LINK = 2015
