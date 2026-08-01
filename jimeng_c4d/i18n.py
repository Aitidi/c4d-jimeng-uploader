"""User-facing Chinese and English strings for the plug-in dialog."""

from __future__ import annotations


LANGUAGE_ZH = "zh"
LANGUAGE_EN = "en"
DEFAULT_LANGUAGE = LANGUAGE_ZH


STRINGS = {
    LANGUAGE_ZH: {
        "dialog_title": "Seedance_c4d_uploader",
        "language_button": "English",
        "label_mode": "上传方式",
        "mode_camera": "相机白模渲染",
        "mode_local": "本地 MP4 上传",
        "label_camera": "相机",
        "label_render_settings": "渲染设置",
        "label_frame_start": "起始帧",
        "label_frame_end": "结束帧",
        "label_output_dir": "MP4 输出路径",
        "label_local_video": "本地 H.264 MP4",
        "button_browse": "选择…",
        "button_refresh": "刷新场景",
        "button_render_settings": "渲染设置",
        "button_reset_settings": "重置渲染设置",
        "button_render_upload": "渲染并上传",
        "button_upload_local": "上传本地 MP4",
        "button_preview": "预览视频",
        "label_link": "即梦链接",
        "button_open_link": "打开即梦链接",
        "button_copy_link": "复制链接",
        "status_ready": "就绪。",
        "status_language_changed": "已切换为中文界面。",
        "status_link_expired": "即梦链接已过期，请重新上传。",
        "status_render_cancelled_unsaved": "已取消渲染：请先保存 C4D 文件。",
        "status_render_not_started_unsaved": "未保存 C4D 文件，未开始渲染。",
        "status_input_changed": "输入已变更；请重新渲染或上传以生成新链接。",
        "status_loading_protocol": "正在读取即梦 DCC 协议…",
        "status_protocol_fallback": "DCC 配置请求失败，已使用内置协议。",
        "status_link_created": "即梦链接已生成（本机桥接将在 30 分钟后失效）。",
        "status_failed": "失败：{message}",
        "status_waiting_output": "渲染已完成，正在等待 C4D 写入 MP4…",
        "status_render_started_synced": "已同步此前 Render Settings 的输出分辨率；已切换到 {preset}，正在使用 C4D Render to Picture Viewer 渲染；完成后会自动恢复原渲染设置并上传。",
        "status_render_started_kept": "已保留 Jimeng 预设的输出分辨率；已切换到 {preset}，正在使用 C4D Render to Picture Viewer 渲染；完成后会自动恢复原渲染设置并上传。",
        "status_native_settings_opened": "已打开 {preset} 的 C4D 原生渲染设置。",
        "status_settings_reset": "已从预设恢复 {preset}；保存路径、自动文件名和 VPR 参数均以预设为准。",
        "status_scene_refreshed": "已刷新场景；帧段和输出路径直接来自 Jimeng Viewport White Model。",
        "status_link_copied": "即梦链接已复制。",
        "question_unsaved_scene": "当前 C4D 场景尚未保存。\n\n渲染预设使用相对路径和 $prj 等文件名变量；请先保存 C4D 文件。\n\n是否现在打开 C4D 的保存对话框？",
        "dialog_select_video": "选择 H.264 MP4",
        "error_no_document": "没有打开的 C4D 场景。",
        "error_render_settings_missing": "无法在当前场景登记 Jimeng Viewport White Model。",
        "error_already_rendering": "C4D 当前正在渲染，请完成后再点击“渲染并上传”。",
        "error_select_camera": "请选择相机。",
        "error_unsupported_camera": "请选择有效的 C4D 标准相机或 Redshift Camera。",
        "error_no_render_view": "无法取得 C4D 渲染视图。",
        "error_no_preview": "没有可预览的视频。",
        "error_link_expired": "即梦链接已失效，请重新上传。",
    },
    LANGUAGE_EN: {
        "dialog_title": "Seedance_c4d_uploader",
        "language_button": "中文",
        "label_mode": "Upload mode",
        "mode_camera": "Camera white-model render",
        "mode_local": "Upload local MP4",
        "label_camera": "Camera",
        "label_render_settings": "Render Settings",
        "label_frame_start": "Start frame",
        "label_frame_end": "End frame",
        "label_output_dir": "Output path",
        "label_local_video": "Local H.264 MP4",
        "button_browse": "Browse…",
        "button_refresh": "Refresh scene",
        "button_render_settings": "Settings",
        "button_reset_settings": "Reset",
        "button_render_upload": "Render & Upload",
        "button_upload_local": "Upload MP4",
        "button_preview": "Preview",
        "label_link": "Jimeng link",
        "button_open_link": "Open Link",
        "button_copy_link": "Copy Link",
        "status_ready": "Ready.",
        "status_language_changed": "Switched to English.",
        "status_link_expired": "The Jimeng link has expired. Upload again.",
        "status_render_cancelled_unsaved": "Rendering cancelled: save the C4D file first.",
        "status_render_not_started_unsaved": "The C4D file was not saved; rendering did not start.",
        "status_input_changed": "Input changed. Render or upload again to create a new link.",
        "status_loading_protocol": "Loading the Jimeng DCC protocol…",
        "status_protocol_fallback": "The DCC configuration request failed; using the built-in protocol.",
        "status_link_created": "Jimeng link created (the local bridge expires in 30 minutes).",
        "status_failed": "Failed: {message}",
        "status_waiting_output": "Rendering finished; waiting for C4D to write the MP4…",
        "status_render_started_synced": "Copied the output resolution from the previous Render Settings; switched to {preset} and started C4D Render to Picture Viewer. The previous settings will be restored before upload.",
        "status_render_started_kept": "Kept the Jimeng preset output resolution; switched to {preset} and started C4D Render to Picture Viewer. The previous settings will be restored before upload.",
        "status_native_settings_opened": "Opened C4D native Render Settings for {preset}.",
        "status_settings_reset": "Restored {preset} from the preset; its output path, filename tokens, and VPR settings are now active.",
        "status_scene_refreshed": "Scene refreshed. Frame range and output path come directly from Jimeng Viewport White Model.",
        "status_link_copied": "Jimeng link copied.",
        "question_unsaved_scene": "The current C4D scene has not been saved.\n\nThe render preset uses relative paths and filename tokens such as $prj. Save the C4D file first.\n\nOpen C4D's Save dialog now?",
        "dialog_select_video": "Select H.264 MP4",
        "error_no_document": "No C4D scene is open.",
        "error_render_settings_missing": "Jimeng Viewport White Model could not be registered in the current scene.",
        "error_already_rendering": "C4D is already rendering. Wait for it to finish before selecting Render and Upload again.",
        "error_select_camera": "Select a camera.",
        "error_unsupported_camera": "Select a valid native C4D camera or Redshift Camera.",
        "error_no_render_view": "Could not obtain a C4D render view.",
        "error_no_preview": "No video is available to preview.",
        "error_link_expired": "The Jimeng link has expired. Upload again.",
    },
}


def normalize_language(value):
    """Return a supported language code, defaulting to Chinese."""
    return value if value in STRINGS else DEFAULT_LANGUAGE


def other_language(value):
    """Return the other supported interface language."""
    return LANGUAGE_EN if normalize_language(value) == LANGUAGE_ZH else LANGUAGE_ZH


def text(language, key, **values):
    """Look up and format a user-facing string without C4D dependencies."""
    selected = STRINGS[normalize_language(language)]
    fallback = STRINGS[DEFAULT_LANGUAGE]
    template = selected.get(key, fallback.get(key, key))
    return template.format(**values)
