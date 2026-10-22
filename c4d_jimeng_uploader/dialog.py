"""GeDialog for rendering through C4D's Picture Viewer and uploading to Jimeng."""

from __future__ import annotations

import os
import time
import webbrowser

import c4d
from c4d import gui, storage

from . import bridge, i18n, media, protocol, renderer, settings
from .constants import (
    ID_APPLY_WHITE_PRESET,
    ID_BROWSE_VIDEO,
    ID_CAMERA,
    ID_COPY_LINK,
    ID_FRAME_END,
    ID_FRAME_START,
    ID_LABEL_CAMERA,
    ID_LABEL_FRAME_END,
    ID_LABEL_FRAME_START,
    ID_LABEL_LINK,
    ID_LABEL_LOCAL_VIDEO,
    ID_LABEL_MODE,
    ID_LABEL_OUTPUT_DIR,
    ID_LABEL_RENDER_SETTINGS,
    ID_LANGUAGE,
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
            "language": i18n.normalize_language(persisted.get("language")),
        }
        self.camera_options = []
        self.render_options = []
        self.render_frame_start = 0
        self.render_frame_end = 0
        self.render_output_path = ""
        self._status_key = "status_ready"
        self._status_values = {}
        self.status = self._t(self._status_key)
        self.last_video_path = ""
        self.bridge_result = None
        self.pending_render = None
        self._initialized = False

    def CreateLayout(self):
        self.SetTitle(self._t("dialog_title"))
        self.GroupBegin(1999, c4d.BFH_SCALEFIT, 1, 1)
        self.GroupBorderSpace(12, 8, 12, 0)
        self.AddButton(ID_LANGUAGE, c4d.BFH_LEFT | c4d.BFH_FIXED, 104, 0, self._t("language_button"))
        self.GroupEnd()
        self.GroupBegin(2000, c4d.BFH_SCALEFIT | c4d.BFV_TOP, 2, 1)
        self.GroupBorderSpace(12, 10, 12, 10)
        self.GroupSpace(8, 6)

        self.AddStaticText(ID_LABEL_MODE, c4d.BFH_SCALEFIT | c4d.BFV_CENTER, 180, 0, self._t("label_mode"))
        self.AddComboBox(ID_MODE, c4d.BFH_SCALEFIT)
        self.AddChild(ID_MODE, MODE_CAMERA, self._t("mode_camera"))
        self.AddChild(ID_MODE, MODE_LOCAL, self._t("mode_local"))

        self.AddStaticText(ID_LABEL_CAMERA, c4d.BFH_SCALEFIT | c4d.BFV_CENTER, 180, 0, self._t("label_camera"))
        self.AddComboBox(ID_CAMERA, c4d.BFH_SCALEFIT, allowfiltering=True)

        self.AddStaticText(ID_LABEL_RENDER_SETTINGS, c4d.BFH_SCALEFIT | c4d.BFV_CENTER, 180, 0, self._t("label_render_settings"))
        self.AddComboBox(ID_RENDER_SETTINGS, c4d.BFH_SCALEFIT, allowfiltering=True)

        self.AddStaticText(ID_LABEL_FRAME_START, c4d.BFH_SCALEFIT | c4d.BFV_CENTER, 180, 0, self._t("label_frame_start"))
        self.AddEditNumberArrows(ID_FRAME_START, c4d.BFH_SCALEFIT)
        self.AddStaticText(ID_LABEL_FRAME_END, c4d.BFH_SCALEFIT | c4d.BFV_CENTER, 180, 0, self._t("label_frame_end"))
        self.AddEditNumberArrows(ID_FRAME_END, c4d.BFH_SCALEFIT)

        self.AddStaticText(ID_LABEL_OUTPUT_DIR, c4d.BFH_SCALEFIT | c4d.BFV_CENTER, 180, 0, self._t("label_output_dir"))
        self.AddEditText(ID_OUTPUT_DIR, c4d.BFH_SCALEFIT)

        self.AddStaticText(ID_LABEL_LOCAL_VIDEO, c4d.BFH_SCALEFIT | c4d.BFV_CENTER, 180, 0, self._t("label_local_video"))
        self.GroupBegin(2011, c4d.BFH_SCALEFIT, 2, 1)
        self.AddEditText(ID_LOCAL_VIDEO, c4d.BFH_SCALEFIT)
        self.AddButton(ID_BROWSE_VIDEO, c4d.BFH_RIGHT, name=self._t("button_browse"))
        self.GroupEnd()
        self.GroupEnd()

        self.GroupBegin(2012, c4d.BFH_SCALEFIT, 3, 1)
        self.GroupBorderSpace(12, 4, 12, 4)
        self.GroupSpace(6, 4)
        self.AddButton(ID_REFRESH, c4d.BFH_SCALEFIT, name=self._t("button_refresh"))
        self.AddButton(ID_NATIVE_RENDER_SETTINGS, c4d.BFH_SCALEFIT, name=self._t("button_render_settings"))
        self.AddButton(ID_APPLY_WHITE_PRESET, c4d.BFH_SCALEFIT, name=self._t("button_reset_settings"))
        self.GroupEnd()

        self.GroupBegin(2013, c4d.BFH_SCALEFIT, 3, 1)
        self.GroupBorderSpace(12, 4, 12, 4)
        self.GroupSpace(6, 4)
        self.AddButton(ID_RENDER_UPLOAD, c4d.BFH_SCALEFIT, name=self._t("button_render_upload"))
        self.AddButton(ID_UPLOAD_LOCAL, c4d.BFH_SCALEFIT, name=self._t("button_upload_local"))
        self.AddButton(ID_PREVIEW, c4d.BFH_SCALEFIT, name=self._t("button_preview"))
        self.GroupEnd()

        self.GroupBegin(2014, c4d.BFH_SCALEFIT, 2, 1)
        self.GroupBorderSpace(12, 4, 12, 4)
        self.AddStaticText(ID_LABEL_LINK, c4d.BFH_SCALEFIT | c4d.BFV_CENTER, 180, 0, self._t("label_link"))
        self.AddEditText(ID_LINK, c4d.BFH_SCALEFIT)
        self.GroupEnd()

        self.GroupBegin(2016, c4d.BFH_SCALEFIT, 2, 1)
        self.GroupBorderSpace(12, 4, 12, 4)
        self.GroupSpace(6, 4)
        self.AddButton(ID_OPEN_LINK, c4d.BFH_SCALEFIT, name=self._t("button_open_link"))
        self.AddButton(ID_COPY_LINK, c4d.BFH_SCALEFIT, name=self._t("button_copy_link"))
        self.GroupEnd()

        self.AddStaticText(ID_STATUS, c4d.BFH_SCALEFIT | c4d.BFV_TOP, 0, 42, "")
        return True

    def InitValues(self):
        self._initialized = True
        self._apply_language()
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
            self._set_status("status_link_expired")
        return True

    def _document(self):
        doc = c4d.documents.GetActiveDocument()
        if doc is None:
            raise RuntimeError(self._t("error_no_document"))
        return doc

    def _ensure_document_saved(self, doc):
        """Require a scene path before rendering a tokenized Save output."""
        if str(doc.GetDocumentPath() or "").strip():
            return True
        if not gui.QuestionDialog(self._t("question_unsaved_scene")):
            self._set_status("status_render_cancelled_unsaved")
            return False
        # Do not inspect CallCommand's return value: C4D UI commands can
        # return False even when their modal dialog was opened successfully.
        c4d.CallCommand(SAVE_DOCUMENT_COMMAND)
        if not str(doc.GetDocumentPath() or "").strip():
            self._set_status("status_render_not_started_unsaved")
            return False
        c4d.EventAdd()
        return True

    def _render_settings_option(self, doc, target):
        for option in renderer.render_setting_entries(doc):
            if option[2] == target:
                return option
        raise RuntimeError(self._t("error_render_settings_missing"))

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

    def _populate_mode_combo(self):
        self.FreeChildren(ID_MODE)
        self.AddChild(ID_MODE, MODE_CAMERA, self._t("mode_camera"))
        self.AddChild(ID_MODE, MODE_LOCAL, self._t("mode_local"))
        self.SetInt32(ID_MODE, int(self.state["mode"]))

    def _write_render_settings_fields(self):
        self.SetInt32(ID_FRAME_START, int(self.render_frame_start))
        self.SetInt32(ID_FRAME_END, int(self.render_frame_end))
        self.SetString(ID_OUTPUT_DIR, self.render_output_path)

    def _write_values(self):
        if not self._initialized:
            return
        self._populate_mode_combo()
        self._populate_combo(ID_CAMERA, self.camera_options, self.state["camera_key"])
        self._populate_combo(ID_RENDER_SETTINGS, self.render_options, self.state["render_settings_key"])
        self.SetInt32(ID_MODE, int(self.state["mode"]))
        self._write_render_settings_fields()
        self.SetString(ID_LOCAL_VIDEO, self.state["local_video"])
        self.SetString(ID_LINK, self.bridge_result.get("redirect_url", "") if self.bridge_result else "")
        self._write_status()
        self._update_enabled()

    def _write_status(self):
        self.status = self._t(self._status_key, **self._status_values)
        self.SetString(ID_STATUS, self.status)

    def _apply_language(self):
        """Refresh every dialog-owned string without rebuilding the dialog."""
        self.SetTitle(self._t("dialog_title"))
        for gadget_id, text_key in (
            (ID_LABEL_MODE, "label_mode"),
            (ID_LABEL_CAMERA, "label_camera"),
            (ID_LABEL_RENDER_SETTINGS, "label_render_settings"),
            (ID_LABEL_FRAME_START, "label_frame_start"),
            (ID_LABEL_FRAME_END, "label_frame_end"),
            (ID_LABEL_OUTPUT_DIR, "label_output_dir"),
            (ID_LABEL_LOCAL_VIDEO, "label_local_video"),
            (ID_LABEL_LINK, "label_link"),
            (ID_LANGUAGE, "language_button"),
            (ID_BROWSE_VIDEO, "button_browse"),
            (ID_REFRESH, "button_refresh"),
            (ID_NATIVE_RENDER_SETTINGS, "button_render_settings"),
            (ID_APPLY_WHITE_PRESET, "button_reset_settings"),
            (ID_RENDER_UPLOAD, "button_render_upload"),
            (ID_UPLOAD_LOCAL, "button_upload_local"),
            (ID_PREVIEW, "button_preview"),
            (ID_OPEN_LINK, "button_open_link"),
            (ID_COPY_LINK, "button_copy_link"),
        ):
            self.SetString(gadget_id, self._t(text_key))
        self._populate_mode_combo()
        self._write_status()
        self.LayoutChanged(2000)

    def _update_enabled(self):
        camera_mode = int(self.state["mode"]) == MODE_CAMERA
        render_pending = self.pending_render is not None
        for gadget in (ID_REFRESH, ID_CAMERA, ID_NATIVE_RENDER_SETTINGS, ID_APPLY_WHITE_PRESET, ID_RENDER_UPLOAD):
            self.Enable(gadget, camera_mode and not render_pending)
        self.Enable(ID_RENDER_SETTINGS, False)
        self.Enable(ID_LANGUAGE, True)
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

    def _t(self, key, **values):
        return i18n.text(self.state["language"], key, **values)

    def _set_status(self, key, **values):
        self._status_key = key
        self._status_values = values
        self._write_status()

    def _toggle_language(self):
        self.state["language"] = i18n.other_language(self.state["language"])
        self._apply_language()
        self._set_status("status_language_changed")

    def _invalidate_link(self):
        if self.bridge_result:
            self.bridge_result = None
            self._set_status("status_input_changed")

    def _load_protocol(self):
        self._set_status("status_loading_protocol")
        config = protocol.fetch_dcc_protocol_config(bridge.DEFAULT_TARGET_URL)
        protocol.validate_export_protocol(config)
        if config.get("source") == "fallback":
            self._set_status("status_protocol_fallback")
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
        self._set_status("status_link_created")
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
        self._set_status("status_failed", message=str(message))
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
                    self._set_status("status_waiting_output")
                    return
                raise
            self.pending_render = None
            self._start_bridge(path, pending["config"])
            self._save_state()
        except Exception as exc:
            self._finish_pending_with_error(exc)

    def _render_upload(self):
        if self._c4d_is_rendering():
            raise RuntimeError(self._t("error_already_rendering"))
        self._read_fields()
        doc = self._document()
        if not self._ensure_document_saved(doc):
            return
        camera = self._selected_camera()
        if not camera:
            raise RuntimeError(self._t("error_select_camera"))
        if not renderer.is_supported_camera(camera):
            raise RuntimeError(self._t("error_unsupported_camera"))

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
            raise RuntimeError(self._t("error_no_render_view"))

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
        self._set_status(
            "status_render_started_synced" if copied_resolution else "status_render_started_kept",
            preset=WHITE_RENDER_SETTINGS_NAME,
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
            self._t("dialog_select_video"),
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
        self._set_status("status_native_settings_opened", preset=WHITE_RENDER_SETTINGS_NAME)

    def _reset_render_settings(self):
        renderer.reset_white_render_settings(self._document())
        c4d.EventAdd()
        self._refresh_scene()
        self._invalidate_link()
        self._set_status("status_settings_reset", preset=WHITE_RENDER_SETTINGS_NAME)

    def Command(self, gadget_id, _msg):
        try:
            if gadget_id == ID_REFRESH:
                self._read_fields()
                self._refresh_scene(ensure_preset=True)
                self._set_status("status_scene_refreshed")
                self._write_values()
                return True
            if gadget_id == ID_LANGUAGE:
                self._toggle_language()
            elif gadget_id == ID_CAMERA:
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
                    raise RuntimeError(self._t("error_no_preview"))
                os.startfile(preview_path)
            elif gadget_id == ID_OPEN_LINK:
                if not self.bridge_result or not bridge.bridge_is_alive(self.bridge_result.get("token"), self.bridge_result.get("expires_at")):
                    raise RuntimeError(self._t("error_link_expired"))
                webbrowser.open(self.bridge_result["redirect_url"], new=2)
            elif gadget_id == ID_COPY_LINK:
                if not self.bridge_result or not bridge.bridge_is_alive(self.bridge_result.get("token"), self.bridge_result.get("expires_at")):
                    raise RuntimeError(self._t("error_link_expired"))
                c4d.CopyStringToClipboard(self.bridge_result["redirect_url"])
                self._set_status("status_link_copied")
            self._save_state()
            self._write_values()
        except Exception as exc:
            if gadget_id in (ID_RENDER_UPLOAD, ID_UPLOAD_LOCAL):
                self.bridge_result = None
            self._set_status("status_failed", message=str(exc))
            self._update_enabled()
            gui.MessageDialog("{0}\n\n{1}".format(self._t("dialog_title"), exc))
        return True
