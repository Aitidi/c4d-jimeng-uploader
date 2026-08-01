"""Render Settings preset and native render helpers for the Jimeng uploader."""

from __future__ import annotations

import glob
import os
import time

import c4d

from . import protocol
from .constants import (
    PRESET_VERSION_CONTAINER_ID,
    RENDER_SETTINGS_PRESET_DIRECTORY,
    WHITE_RENDER_SETTINGS_NAME,
)


class RenderError(RuntimeError):
    pass


def _walk_nodes(first):
    node = first
    while node:
        yield node
        child = node.GetDown()
        if child:
            for descendant in _walk_nodes(child):
                yield descendant
        node = node.GetNext()


def _object_key(op):
    names = []
    current = op
    while current:
        names.append(current.GetName())
        current = current.GetUp()
    return "/".join(reversed(names))


def is_supported_camera(op):
    """Return whether *op* is a native or Redshift camera object."""
    if op is None:
        return False
    try:
        if op.CheckType(c4d.Ocamera):
            return True
    except Exception:
        return False

    redshift_camera_type = getattr(c4d, "Orscamera", None)
    if redshift_camera_type is not None:
        try:
            if op.GetType() == redshift_camera_type:
                return True
        except Exception:
            pass

    try:
        type_name = str(op.GetTypeName()).casefold()
    except Exception:
        type_name = ""
    return "redshift" in type_name and "camera" in type_name


def camera_entries(doc):
    entries = []
    for op in _walk_nodes(doc.GetFirstObject()):
        if is_supported_camera(op):
            entries.append((_object_key(op), op.GetName(), op))
    return entries


def find_camera(doc, key):
    for current_key, _label, camera in camera_entries(doc):
        if current_key == key:
            return camera
    return None


def _render_data_entries(doc):
    return list(_walk_nodes(doc.GetFirstRenderData()))


def render_setting_entries(doc):
    result = []
    for index, render_data in enumerate(_render_data_entries(doc)):
        name = render_data.GetName() or "Render Settings {0}".format(index + 1)
        result.append(("{0}:{1}".format(index, name), name, render_data))
    return result


def find_render_settings(doc, key):
    for candidate_key, _name, render_data in render_setting_entries(doc):
        if candidate_key == key:
            return render_data
    return None


def default_render_settings(doc):
    """Return the scene-local copy of the user supplied Render Settings preset."""
    for _key, name, render_data in render_setting_entries(doc):
        if name == WHITE_RENDER_SETTINGS_NAME:
            return render_data
    return None


def _preset_asset_path():
    """Find the actual Render Settings asset in the supplied AssetDB export."""
    pattern = os.path.join(RENDER_SETTINGS_PRESET_DIRECTORY, "preset_*", "1", "asset")
    candidates = []
    for path in glob.glob(pattern):
        info_path = os.path.join(os.path.dirname(os.path.dirname(path)), "asset.info")
        try:
            with open(info_path, "r", encoding="utf-8") as stream:
                asset_info = [line.strip() for line in stream if line.strip()]
        except OSError:
            continue
        if asset_info and asset_info[-1] == "net.maxon.assettype.preset.rendersettings":
            candidates.append(path)
    if len(candidates) != 1:
        raise RenderError(
            "未找到唯一的 Render Settings 预设。请确认目录存在且未损坏：{0}".format(
                RENDER_SETTINGS_PRESET_DIRECTORY
            )
        )
    return candidates[0]


def _preset_fingerprint():
    """Return the version stored by the Asset Browser next to the asset."""
    asset_path = _preset_asset_path()
    hash_path = os.path.join(os.path.dirname(asset_path), "hash")
    try:
        with open(hash_path, "rb") as stream:
            version = stream.read().strip().decode("ascii", "replace")
    except OSError:
        version = ""
    if not version:
        version = str(os.stat(asset_path).st_mtime_ns)
    return version


def _load_preset_render_data():
    """Load a clone of the Asset Browser preset without adding it as a document."""
    flags = c4d.SCENEFILTER_ONLY_RENDERDATA | c4d.SCENEFILTER_DONTCORRECTOUTPUTFORMAT
    preset_doc = c4d.documents.LoadDocument(_preset_asset_path(), flags)
    if preset_doc is None:
        raise RenderError("C4D 无法读取 Jimeng Viewport White Model 渲染预设。")
    try:
        source = preset_doc.GetActiveRenderData() or preset_doc.GetFirstRenderData()
        if source is None:
            raise RenderError("Render Settings 预设中没有可用的渲染设置。")
        clone = source.GetClone(c4d.COPYFLAGS_NONE)
        if clone is None:
            raise RenderError("无法复制 Render Settings 预设。")
        clone.SetName(WHITE_RENDER_SETTINGS_NAME)
        return clone
    finally:
        c4d.documents.KillDocument(preset_doc)


def ensure_white_render_settings(doc):
    """Insert or update the scene copy from the user supplied asset preset."""
    fingerprint = _preset_fingerprint()
    existing = default_render_settings(doc)
    if existing is not None:
        if str(existing[PRESET_VERSION_CONTAINER_ID] or "") != fingerprint:
            return reset_white_render_settings(doc, existing, fingerprint)
        return existing
    render_data = _load_preset_render_data()
    doc.InsertRenderDataLast(render_data)
    render_data[PRESET_VERSION_CONTAINER_ID] = fingerprint
    render_data.Message(c4d.MSG_UPDATE)
    return render_data


def reset_white_render_settings(doc, target=None, fingerprint=None):
    """Restore the scene copy to the exact settings held by the preset asset."""
    target = target or default_render_settings(doc)
    if target is None:
        target = _load_preset_render_data()
        doc.InsertRenderDataLast(target)
    source = _load_preset_render_data()
    source_data = source.GetDataInstance()
    if source_data is None:
        raise RenderError("Render Settings 预设不包含可复制的参数。")
    target.SetData(source_data.GetClone(c4d.COPYFLAGS_NONE), False)
    target.SetName(WHITE_RENDER_SETTINGS_NAME)
    target[PRESET_VERSION_CONTAINER_ID] = fingerprint or _preset_fingerprint()
    target.Message(c4d.MSG_UPDATE)
    return target


def is_viewport_renderer(render_data):
    return int(render_data[c4d.RDATA_RENDERENGINE] or 0) == c4d.RDATA_RENDERENGINE_PREVIEWHARDWARE


def original_resolution(render_data):
    width = int(render_data[c4d.RDATA_XRES] or 0)
    height = int(render_data[c4d.RDATA_YRES] or 0)
    if width <= 0 or height <= 0:
        raise RenderError("所选 Render Settings 没有有效的输出分辨率。")
    return width, height


def copy_output_resolution(source_render_data, target_render_data):
    """Copy only Output width and height from one native RenderData to another."""
    width, height = original_resolution(source_render_data)
    target_render_data[c4d.RDATA_XRES] = width
    target_render_data[c4d.RDATA_YRES] = height
    target_render_data.Message(c4d.MSG_UPDATE)
    return width, height


def render_fps(doc, render_data):
    if bool(render_data[c4d.RDATA_FRAMERATE_SYNC_WITH_PROJECT]):
        return int(doc.GetFps())
    fps = int(render_data[c4d.RDATA_FRAMERATE] or 0)
    return fps if fps > 0 else int(doc.GetFps())


def render_frame_range(doc, render_data):
    """Read the frame range as configured in the selected Render Settings."""
    fps = render_fps(doc, render_data)
    try:
        start = int(render_data[c4d.RDATA_FRAMEFROM].GetFrame(fps))
        end = int(render_data[c4d.RDATA_FRAMETO].GetFrame(fps))
    except AttributeError:
        raise RenderError("所选 Render Settings 没有有效的帧范围。")
    return start, end


def render_output_path(render_data):
    path = str(render_data[c4d.RDATA_PATH] or "").strip()
    if not path:
        raise RenderError("请先在原生 Render Settings 的 Save 页面设置 MP4 文件路径。")
    return path


def _resolved_output_path(doc, configured_path):
    """Resolve only the directory part C4D can determine before token expansion."""
    value = os.path.expandvars(configured_path.replace("/", os.sep))
    if os.path.isabs(value):
        return os.path.normpath(value)
    document_path = doc.GetDocumentPath()
    # C4D resolves relative Save paths against the saved scene. For an
    # unsaved scene it uses its current process directory, which is also the
    # best available path to search without modifying the user setting.
    base = document_path or os.getcwd()
    return os.path.normpath(os.path.join(base, value))


def _output_locations(doc, render_data):
    configured_path = _resolved_output_path(doc, render_output_path(render_data))
    direct_paths = set()
    directories = set()
    root, extension = os.path.splitext(configured_path)
    has_tokens = "$" in configured_path
    if extension.casefold() == ".mp4":
        if not has_tokens:
            direct_paths.add(configured_path)
        directories.add(os.path.dirname(configured_path))
    elif os.path.isdir(configured_path):
        directories.add(configured_path)
        directories.add(os.path.dirname(configured_path))
    else:
        if not has_tokens:
            direct_paths.add(configured_path + ".mp4")
        directories.add(os.path.dirname(configured_path))
    return direct_paths, {directory for directory in directories if directory}


def _file_stamp(path):
    stat = os.stat(path)
    return stat.st_mtime_ns, stat.st_size


def _snapshot_mp4s(direct_paths, directories):
    snapshot = {}
    for path in direct_paths:
        if os.path.isfile(path):
            snapshot[os.path.normcase(os.path.abspath(path))] = _file_stamp(path)
    for directory in directories:
        if not os.path.isdir(directory):
            continue
        for path in glob.glob(os.path.join(directory, "*.mp4")):
            if os.path.isfile(path):
                snapshot[os.path.normcase(os.path.abspath(path))] = _file_stamp(path)
    return snapshot


def capture_output_snapshot(doc, render_data):
    """Capture possible MP4 outputs before C4D starts the Picture Viewer job."""
    direct_paths, directories = _output_locations(doc, render_data)
    return direct_paths, directories, _snapshot_mp4s(direct_paths, directories)


def find_generated_mp4(direct_paths, directories, before, started_at):
    """Return the new MP4 created by C4D's Save page, if it is available."""
    candidates = []
    for path in direct_paths:
        if os.path.isfile(path):
            candidates.append(os.path.abspath(path))
    for directory in directories:
        if not os.path.isdir(directory):
            continue
        candidates.extend(
            os.path.abspath(path)
            for path in glob.glob(os.path.join(directory, "*.mp4"))
            if os.path.isfile(path)
        )
    changed = []
    for path in set(candidates):
        key = os.path.normcase(path)
        stamp = _file_stamp(path)
        if before.get(key) != stamp or stamp[0] >= started_at:
            changed.append((stamp[0], path))
    if changed:
        return max(changed)[1]
    raise RenderError(
        "C4D 已完成渲染，但未在 Render Settings 的 Save 路径找到新 MP4。"
        "请确认 Save 已启用、Format 是 MP4/H.264，且输出目录可写入。"
    )


def validate_native_render_settings(doc, render_data, config):
    """Validate without changing any Render Settings values."""
    if not is_viewport_renderer(render_data):
        raise RenderError("Jimeng Viewport White Model 的 Renderer 必须是 Viewport Renderer。")
    if not bool(render_data[c4d.RDATA_SAVEIMAGE]):
        raise RenderError("请先在原生 Render Settings 的 Save 页面启用 Save。")
    protocol.validate_export_protocol(config)
    start_frame, end_frame = render_frame_range(doc, render_data)
    protocol.validate_frame_range(config, start_frame, end_frame)
    original_resolution(render_data)
    render_output_path(render_data)
    return capture_output_snapshot(doc, render_data)


_NATIVE_RENDER_SETTINGS_COMMAND = None


def open_native_render_settings():
    """Open C4D's own Edit Render Settings window without guessing an ID.

    The command ID is not exposed as a stable Python constant. Its name is,
    so resolve it from C4D's Command Manager at runtime. This also avoids the
    common mistake of using command 12099, which is Render to Picture Viewer.
    """
    global _NATIVE_RENDER_SETTINGS_COMMAND
    if _NATIVE_RENDER_SETTINGS_COMMAND is None:
        for command_id in range(12000, 13001):
            try:
                name = str(c4d.GetCommandName(command_id) or "").casefold()
            except Exception:
                continue
            if name in {"edit render settings", "render settings"}:
                _NATIVE_RENDER_SETTINGS_COMMAND = command_id
                break
            if ("render" in name and "settings" in name) or "rendereinstellungen" in name:
                _NATIVE_RENDER_SETTINGS_COMMAND = command_id
                break
            if "渲染" in name and "设置" in name:
                _NATIVE_RENDER_SETTINGS_COMMAND = command_id
                break
    if _NATIVE_RENDER_SETTINGS_COMMAND is None:
        raise RenderError("无法定位 C4D 的“编辑渲染设置”命令。请用 Ctrl+B 打开。")
    # Like Render to Picture Viewer, this UI command is asynchronous and can
    # report False despite having opened the window. Dispatching it is enough.
    c4d.CallCommand(_NATIVE_RENDER_SETTINGS_COMMAND)
