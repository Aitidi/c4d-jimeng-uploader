"""GeDialog for rendering through C4D's Picture Viewer and uploading to Jimeng."""

from __future__ import annotations

import os
import time
import webbrowser

import c4d
from c4d import gui, storage

from . import bridge, media, protocol, renderer, settings
from .constants import (
    ID_APPLY_WHITE_PRESET,
    ID_BROWSE_VIDEO,
    ID_CAMERA,
    ID_COPY_LINK,
    ID_FRAME_END,
    ID_FRAME_START,
    ID_LINK,
    ID_LOCAL_VIDEO,
    ID_MODE,
    ID_NATIVE_RENDER_SETTINGS,
    ID_OPEN_LINK,
    ID_OUTPUT_DIR,
    ID_PREVIEW,
    ID_REFRESH,
    ID_RENDER_SETTINGS,
    ID_RENDER_UPLOAD,
    ID_STATUS,
    ID_UPLOAD_LOCAL,
    MODE_CAMERA,
    MODE_LOCAL,
    PLUGIN_NAME,
    RENDER_TO_PICTURE_VIEWER_COMMAND,
    SAVE_DOCUMENT_COMMAND,
    WHITE_RENDER_SETTINGS_NAME,
)


class UploaderDialog(gui.GeDialog):
    def __init__(self):
        super().__init__()
        persisted = settings.load()
        self.state = {
            "mode": int(persisted.get("mode", MODE_CAMERA)),
            "camera_key": str(persisted.get("camera_key", "")),
            "render_settings_key": str(persisted.get("render_settings_key", "")),
            "local_video": str(persisted.get("local_video", "")),
        }
        self.camera_options = []
        self.render_options = []
        self.render_frame_start = 0
        self.render_frame_end = 0
        self.render_output_path = ""
        self.status = "就绪。"
        self.last_video_path = ""
        self.bridge_result = None
        self.pending_render = None
        self._initialized = False

    def CreateLayout(self):
        self.SetTitle(PLUGIN_NAME)
        self.GroupBegin(2000, c4d.BFH_SCALEFIT | c4d.BFV_TOP, 2, 1)
        self.GroupBorderSpace(12, 10, 12, 10)

        self.AddStaticText(2001, c4d.BFH_LEFT | c4d.BFV_CENTER, name="上传方式")
        self.AddComboBox(ID_MODE, c4d.BFH_SCALEFIT)
        self.AddChild(ID_MODE, MODE_CAMERA, "相机白模渲染")
        self.AddChild(ID_MODE, MODE_LOCAL, "本地 MP4 上传")

        self.AddStaticText(2002, c4d.BFH_LEFT | c4d.BFV_CENTER, name="相机")
        self.AddComboBox(ID_CAMERA, c4d.BFH_SCALEFIT, allowfiltering=True)

        self.AddStaticText(2003, c4d.BFH_LEFT | c4d.BFV_CENTER, name="Render Settings（固定预设）")
        self.AddComboBox(ID_RENDER_SETTINGS, c4d.BFH_SCALEFIT, allowfiltering=True)

        self.AddStaticText(2005, c4d.BFH_LEFT | c4d.BFV_CENTER, name="起始帧（Render Settings）")
        self.AddEditNumberArrows(ID_FRAME_START, c4d.BFH_SCALEFIT)
        self.AddStaticText(2006, c4d.BFH_LEFT | c4d.BFV_CENTER, name="结束帧（Render Settings）")
        self.AddEditNumberArrows(ID_FRAME_END, c4d.BFH_SCALEFIT)

        self.AddStaticText(2007, c4d.BFH_LEFT | c4d.BFV_CENTER, name="MP4 输出路径（Render Settings）")
        self.AddEditText(ID_OUTPUT_DIR, c4d.BFH_SCALEFIT)

        self.AddStaticText(2010, c4d.BFH_LEFT | c4d.BFV_CENTER, name="本地 H.264 MP4")
        self.GroupBegin(2011, c4d.BFH_SCALEFIT, 2, 1)
        self.AddEditText(ID_LOCAL_VIDEO, c4d.BFH_SCALEFIT)
        self.AddButton(ID_BROWSE_VIDEO, c4d.BFH_RIGHT, name="选择…")
        self.GroupEnd()
        self.GroupEnd()

        self.GroupBegin(2012, c4d.BFH_SCALEFIT, 3, 1)
        self.GroupBorderSpace(12, 4, 12, 4)
        self.AddButton(ID_REFRESH, c4d.BFH_LEFT, name="刷新场景")
        self.AddButton(ID_NATIVE_RENDER_SETTINGS, c4d.BFH_LEFT, name="渲染设置")
        self.AddButton(ID_APPLY_WHITE_PRESET, c4d.BFH_RIGHT, name="重置渲染设置")
        self.GroupEnd()

        self.GroupBegin(2013, c4d.BFH_SCALEFIT, 3, 1)
        self.GroupBorderSpace(12, 4, 12, 4)
        self.AddButton(ID_RENDER_UPLOAD, c4d.BFH_LEFT, name="渲染并上传")
        self.AddButton(ID_UPLOAD_LOCAL, c4d.BFH_LEFT, name="上传本地 MP4")
        self.AddButton(ID_PREVIEW, c4d.BFH_RIGHT, name="预览视频")
        self.GroupEnd()

        self.GroupBegin(2014, c4d.BFH_SCALEFIT, 2, 1)
        self.GroupBorderSpace(12, 4, 12, 4)
        self.AddStaticText(2015, c4d.BFH_LEFT | c4d.BFV_CENTER, name="即梦链接")
        self.AddEditText(ID_LINK, c4d.BFH_SCALEFIT)
        self.GroupEnd()

        self.GroupBegin(2016, c4d.BFH_SCALEFIT, 2, 1)
        self.GroupBorderSpace(12, 4, 12, 4)
        self.AddButton(ID_OPEN_LINK, c4d.BFH_LEFT, name="打开即梦链接")
        self.AddButton(ID_COPY_LINK, c4d.BFH_RIGHT, name="复制链接")
        self.GroupEnd()

        self.AddStaticText(ID_STATUS, c4d.BFH_SCALEFIT | c4d.BFV_TOP, 0, 42, "")
        return True

    def InitValues(self):
        self._initialized = True
        self._refresh_scene(ensure_preset=True)
        self._write_values()
        self.SetTimer(1000)
        return True

    def CoreMessage(self, message_id, _msg):
        if message_id == c4d.EVMSG_RAYTRACER_FINISHED and self.pending_render:
            self.pending_render["render_finished"] = True
        return True

    def Timer(self, _msg):
        if self.pending_render:
            self._poll_pending_render()
        if self._initialized and not self.pending_render:
            before = (self.render_frame_start, self.render_frame_end, self.render_output_path)
            self._sync_render_settings_fields()
            if before != (self.render_frame_start, self.render_frame_end, self.render_output_path):
                self._write_render_settings_fields()
        if self.bridge_result and not bridge.bridge_is_alive(self.bridge_result.get("token"), self.bridge_result.get("expires_at")):
            self.bridge_result = None
            self.status = "即梦链接已过期，请重新上传。"
            self._write_status()
        return True

    def _document(self):
        doc = c4d.documents.GetActiveDocument()
        if doc is None:
            raise RuntimeError("没有打开的 C4D 场景。")
        return doc

    def _ensure_document_saved(self, doc):
        """Require a scene path before rendering a tokenized Save output."""
        if str(doc.GetDocumentPath() or "").strip():
            return True
        if not gui.QuestionDialog(
            "当前 C4D 场景尚未保存。\n\n"
            "渲染预设使用相对路径和 $prj 等文件名变量；请先保存 C4D 文件。\n\n"
            "是否现在打开 C4D 的保存对话框？"
        ):
            self._set_status("已取消渲染：请先保存 C4D 文件。")
            return False
        # Do not inspect CallCommand's return value: C4D UI commands can
        # return False even when their modal dialog was opened successfully.
        c4d.CallCommand(SAVE_DOCUMENT_COMMAND)
        if not str(doc.GetDocumentPath() or "").strip():
            self._set_status("未保存 C4D 文件，未开始渲染。")
            return False
        c4d.EventAdd()
        return True

    def _render_settings_option(self, doc, target):
        for option in renderer.render_setting_entries(doc):
            if option[2] == target:
                return option
        raise RuntimeError("无法在当前场景登记 Jimeng Viewport White Model。")

    def _refresh_scene(self, ensure_preset=False):
        doc = self._document()
        target = renderer.ensure_white_render_settings(doc) if ensure_preset else renderer.default_render_settings(doc)
        if target is None:
            target = renderer.ensure_white_render_settings(doc)
        self.camera_options = renderer.camera_entries(doc)
        # The preset is intentionally the only selectable Render Settings.
        # It prevents the visible fields and the actual Render to Picture
        # Viewer job from silently referring to two different settings.
        self.render_options = [self._render_settings_option(doc, target)]
        camera_keys = {item[0] for item in self.camera_options}
        if self.state["camera_key"] not in camera_keys:
            active = doc.GetRenderBaseDraw().GetSceneCamera(doc) if doc.GetRenderBaseDraw() else None
            self.state["camera_key"] = next(
                (key for key, _label, camera in self.camera_options if camera == active),
                self.camera_options[0][0] if self.camera_options else "",
            )
        self.state["render_settings_key"] = self.render_options[0][0]
        self._sync_render_settings_fields()

    def _sync_render_settings_fields(self):
        try:
            doc = self._document()
            render_data = self._selected_render_settings(doc)
            self.render_frame_start, self.render_frame_end = renderer.render_frame_range(doc, render_data)
            self.render_output_path = str(render_data[c4d.RDATA_PATH] or "")
        except Exception:
            # Validation is intentionally deferred to the buttons, keeping
            # these values passive mirrors of C4D's own Render Settings.
            self.render_frame_start = 0
            self.render_frame_end = 0
            self.render_output_path = ""

    def _populate_combo(self, gadget_id, values, selected_key):
        self.FreeChildren(gadget_id)
        selected_index = 0
        for index, (key, label, _value) in enumerate(values):
            self.AddChild(gadget_id, index, label)
            if key == selected_key:
                selected_index = index
        self.SetInt32(gadget_id, selected_index)

    def _write_render_settings_fields(self):
        self.SetInt32(ID_FRAME_START, int(self.render_frame_start))
        self.SetInt32(ID_FRAME_END, int(self.render_frame_end))
        self.SetString(ID_OUTPUT_DIR, self.render_output_path)

    def _write_values(self):
        if not self._initialized:
            return
        self._populate_combo(ID_CAMERA, self.camera_options, self.state["camera_key"])
        self._populate_combo(ID_RENDER_SETTINGS, self.render_options, self.state["render_settings_key"])
        self.SetInt32(ID_MODE, int(self.state["mode"]))
        self._write_render_settings_fields()
        self.SetString(ID_LOCAL_VIDEO, self.state["local_video"])
        self.SetString(ID_LINK, self.bridge_result.get("redirect_url", "") if self.bridge_result else "")
        self._write_status()
        self._update_enabled()

    def _write_status(self):
        self.SetString(ID_STATUS, self.status)

    def _update_enabled(self):
        camera_mode = int(self.state["mode"]) == MODE_CAMERA
        render_pending = self.pending_render is not None
        for gadget in (ID_REFRESH, ID_CAMERA, ID_NATIVE_RENDER_SETTINGS, ID_APPLY_WHITE_PRESET, ID_RENDER_UPLOAD):
            self.Enable(gadget, camera_mode and not render_pending)
        self.Enable(ID_RENDER_SETTINGS, False)
        self.Enable(ID_MODE, not render_pending)
        for gadget in (ID_FRAME_START, ID_FRAME_END, ID_OUTPUT_DIR):
            self.Enable(gadget, False)
        for gadget in (ID_LOCAL_VIDEO, ID_BROWSE_VIDEO, ID_UPLOAD_LOCAL):
            self.Enable(gadget, not camera_mode and not render_pending)
        ready = bool(self.bridge_result and bridge.bridge_is_alive(self.bridge_result.get("token"), self.bridge_result.get("expires_at")))
        self.Enable(ID_OPEN_LINK, ready)
        self.Enable(ID_COPY_LINK, ready)
        preview_path = self.last_video_path
        if not preview_path and not camera_mode:
            preview_path = os.path.abspath(self.state["local_video"]) if self.state["local_video"] else ""
        self.Enable(ID_PREVIEW, bool(preview_path and os.path.isfile(preview_path)))
        self.Enable(ID_LINK, False)

    def _read_fields(self):
        self.state["mode"] = int(self.GetInt32(ID_MODE) or MODE_CAMERA)
        self.state["local_video"] = str(self.GetString(ID_LOCAL_VIDEO) or "").strip()

    def _save_state(self):
        settings.save(self.state)

    def _selected_camera(self):
        return renderer.find_camera(self._document(), self.state["camera_key"])

    def _selected_render_settings(self, doc=None):
        document = doc or self._document()
        target = renderer.default_render_settings(document)
        if target is None:
            target = renderer.ensure_white_render_settings(document)
        return target

    def _set_status(self, value):
        self.status = value
        self._write_status()

    def _invalidate_link(self):
        if self.bridge_result:
            self.bridge_result = None
            self.status = "输入已变更；请重新渲染或上传以生成新链接。"

    def _load_protocol(self):
        self._set_status("正在读取即梦 DCC 协议…")
        config = protocol.fetch_dcc_protocol_config(bridge.DEFAULT_TARGET_URL)
        protocol.validate_export_protocol(config)
        if config.get("source") == "fallback":
            self._set_status("DCC 配置请求失败，已使用内置协议。")
        return config

    def _start_bridge(self, path, config):
        protocol.validate_file_size(path, config)
        media.inspect_h264_mp4(path)
        self.last_video_path = path
        # The Jimeng page currently ignores the prompt returned by the bridge,
        # so the plug-in deliberately exposes no misleading prompt control.
        # Retain the protocol default in the payload for compatibility.
        export_prompt = protocol.prompt_for_export(config, "")
        self.bridge_result = bridge.start_local_bridge(path, export_prompt)
        self._set_status("即梦链接已生成（本机桥接将在 30 分钟后失效）。")
        self._write_values()

    @staticmethod
    def _c4d_is_rendering():
        return bool(
            c4d.CheckIsRunning(c4d.CHECKISRUNNING_EDITORRENDERING)
            or c4d.CheckIsRunning(c4d.CHECKISRUNNING_EXTERNALRENDERING)
        )

    def _restore_pending_render_context(self, pending):
        if pending.get("restored"):
            return
        try:
            pending["document"].SetActiveRenderData(pending["previous_render_data"])
            pending["base_draw"].SetSceneCamera(pending["previous_camera"])
            c4d.EventAdd()
        finally:
            pending["restored"] = True

    def _finish_pending_with_error(self, message):
        pending = self.pending_render
        if pending:
            self._restore_pending_render_context(pending)
        self.pending_render = None
        self.bridge_result = None
        self._set_status("失败：{0}".format(message))
        self._write_values()

    def _poll_pending_render(self):
        pending = self.pending_render
        if pending is None:
            return
        try:
            running = self._c4d_is_rendering()
            if running:
                pending["saw_rendering"] = True
                return
            if not (pending["render_finished"] or pending["saw_rendering"]):
                return
            self._restore_pending_render_context(pending)
            try:
                path = renderer.find_generated_mp4(
                    pending["direct_paths"],
                    pending["directories"],
                    pending["before"],
                    pending["started_at"],
                )
            except renderer.RenderError:
                # C4D's MP4 writer can still be flushing after its render-end
                # event. Keep polling briefly without changing the user path.
                if time.monotonic() < pending["output_deadline"]:
                    self._set_status("渲染已完成，正在等待 C4D 写入 MP4…")
                    return
                raise
            self.pending_render = None
            self._start_bridge(path, pending["config"])
            self._save_state()
        except Exception as exc:
            self._finish_pending_with_error(exc)

    def _render_upload(self):
        if self._c4d_is_rendering():
            raise RuntimeError("C4D 当前正在渲染，请完成后再点击“渲染并上传”。")
        self._read_fields()
        doc = self._document()
        if not self._ensure_document_saved(doc):
            return
        camera = self._selected_camera()
        if not camera:
            raise RuntimeError("请选择相机。")
        if not renderer.is_supported_camera(camera):
            raise RuntimeError("请选择有效的 C4D 标准相机或 Redshift Camera。")

        target = self._selected_render_settings(doc)
        previous_render_data = doc.GetActiveRenderData()
        copied_resolution = False
        if previous_render_data is not None and previous_render_data != target:
            renderer.copy_output_resolution(previous_render_data, target)
            copied_resolution = True
            self._sync_render_settings_fields()
        config = self._load_protocol()
        direct_paths, directories, before = renderer.validate_native_render_settings(doc, target, config)
        base_draw = doc.GetRenderBaseDraw() or doc.GetActiveBaseDraw()
        if base_draw is None:
            raise RuntimeError("无法取得 C4D 渲染视图。")

        # This is the only temporary scene change. Render to Picture Viewer
        # reads the active RenderData, so switch to the named preset before
        # invoking C4D's own command and remember what must be restored.
        previous_camera = base_draw.GetSceneCamera(doc)
        started_at = time.time_ns()
        self.pending_render = {
            "document": doc,
            "base_draw": base_draw,
            "previous_render_data": previous_render_data,
            "previous_camera": previous_camera,
            "direct_paths": direct_paths,
            "directories": directories,
            "before": before,
            "started_at": started_at,
            "config": config,
            "render_finished": False,
            "saw_rendering": False,
            "restored": False,
            "output_deadline": time.monotonic() + 45.0,
        }
        try:
            doc.SetActiveRenderData(target)
            base_draw.SetSceneCamera(camera)
            c4d.EventAdd()
            # In C4D 2026 this command can return False even after it has
            # successfully opened Picture Viewer and started rendering. The
            # completion event / render-running state below is authoritative.
            c4d.CallCommand(RENDER_TO_PICTURE_VIEWER_COMMAND)
        except Exception:
            self._restore_pending_render_context(self.pending_render)
            self.pending_render = None
            raise
        self._invalidate_link()
        resolution_note = "已同步此前 Render Settings 的输出分辨率；" if copied_resolution else "已保留 Jimeng 预设的输出分辨率；"
        self._set_status(
            "{0}已切换到 {1}，正在使用 C4D Render to Picture Viewer 渲染；完成后会自动恢复原渲染设置并上传。".format(
                resolution_note, WHITE_RENDER_SETTINGS_NAME
            )
        )

    def _upload_local(self):
        self._read_fields()
        path = os.path.abspath(self.state["local_video"])
        config = self._load_protocol()
        self._start_bridge(path, config)
        self._save_state()

    def _browse_video(self):
        path = storage.LoadDialog(
            c4d.FILESELECTTYPE_ANYTHING,
            "选择 H.264 MP4",
            c4d.FILESELECT_LOAD,
            force_suffix="mp4",
            def_path=os.path.dirname(self.state["local_video"]),
        )
        if path:
            self.state["local_video"] = path
            self.SetString(ID_LOCAL_VIDEO, path)
            self._invalidate_link()

    def _open_render_settings(self):
        doc = self._document()
        target = self._selected_render_settings(doc)
        doc.SetActiveRenderData(target)
        c4d.EventAdd()
        renderer.open_native_render_settings()
        self._set_status("已打开 {0} 的 C4D 原生渲染设置。".format(WHITE_RENDER_SETTINGS_NAME))

    def _reset_render_settings(self):
        renderer.reset_white_render_settings(self._document())
        c4d.EventAdd()
        self._refresh_scene()
        self._invalidate_link()
        self._set_status("已从预设恢复 {0}；保存路径、自动文件名和 VPR 参数均以预设为准。".format(WHITE_RENDER_SETTINGS_NAME))

    def Command(self, gadget_id, _msg):
        try:
            if gadget_id == ID_REFRESH:
                self._read_fields()
                self._refresh_scene(ensure_preset=True)
                self._set_status("已刷新场景；帧段和输出路径直接来自 Jimeng Viewport White Model。")
                self._write_values()
                return True
            if gadget_id == ID_CAMERA:
                index = int(self.GetInt32(ID_CAMERA) or 0)
                if 0 <= index < len(self.camera_options):
                    self.state["camera_key"] = self.camera_options[index][0]
                    self._invalidate_link()
            elif gadget_id in (ID_MODE, ID_LOCAL_VIDEO):
                self._read_fields()
                self._invalidate_link()
            elif gadget_id == ID_BROWSE_VIDEO:
                self._browse_video()
            elif gadget_id == ID_APPLY_WHITE_PRESET:
                self._reset_render_settings()
            elif gadget_id == ID_NATIVE_RENDER_SETTINGS:
                self._open_render_settings()
            elif gadget_id == ID_RENDER_UPLOAD:
                self._render_upload()
            elif gadget_id == ID_UPLOAD_LOCAL:
                self._upload_local()
            elif gadget_id == ID_PREVIEW:
                preview_path = self.last_video_path
                if not preview_path and int(self.state["mode"]) == MODE_LOCAL:
                    preview_path = os.path.abspath(self.state["local_video"])
                if not preview_path or not os.path.isfile(preview_path):
                    raise RuntimeError("没有可预览的视频。")
                os.startfile(preview_path)
            elif gadget_id == ID_OPEN_LINK:
                if not self.bridge_result or not bridge.bridge_is_alive(self.bridge_result.get("token"), self.bridge_result.get("expires_at")):
                    raise RuntimeError("即梦链接已失效，请重新上传。")
                webbrowser.open(self.bridge_result["redirect_url"], new=2)
            elif gadget_id == ID_COPY_LINK:
                if not self.bridge_result or not bridge.bridge_is_alive(self.bridge_result.get("token"), self.bridge_result.get("expires_at")):
                    raise RuntimeError("即梦链接已失效，请重新上传。")
                c4d.CopyStringToClipboard(self.bridge_result["redirect_url"])
                self._set_status("即梦链接已复制。")
            self._save_state()
            self._write_values()
        except Exception as exc:
            if gadget_id in (ID_RENDER_UPLOAD, ID_UPLOAD_LOCAL):
                self.bridge_result = None
            self._set_status("失败：{0}".format(exc))
            self._update_enabled()
            gui.MessageDialog("即梦上传器\n\n{0}".format(exc))
        return True
