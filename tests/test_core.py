"""Pure-Python smoke tests for the transport and protocol layers."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
import urllib.request
from unittest import mock


PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PLUGIN_ROOT not in sys.path:
    sys.path.insert(0, PLUGIN_ROOT)

from c4d_jimeng_uploader import bridge, i18n, media, protocol, settings


class LocalizationTests(unittest.TestCase):
    def test_language_normalization_and_toggle(self):
        self.assertEqual(i18n.normalize_language("en"), i18n.LANGUAGE_EN)
        self.assertEqual(i18n.normalize_language("unsupported"), i18n.LANGUAGE_ZH)
        self.assertEqual(i18n.other_language(i18n.LANGUAGE_ZH), i18n.LANGUAGE_EN)
        self.assertEqual(i18n.other_language(i18n.LANGUAGE_EN), i18n.LANGUAGE_ZH)

    def test_translated_button_and_status(self):
        self.assertEqual(i18n.text("zh", "language_button"), "English")
        self.assertEqual(i18n.text("en", "language_button"), "中文")
        self.assertEqual(i18n.text("en", "status_failed", message="test"), "Failed: test")

    def test_all_translation_keys_exist_in_both_languages(self):
        self.assertEqual(
            set(i18n.STRINGS[i18n.LANGUAGE_ZH]),
            set(i18n.STRINGS[i18n.LANGUAGE_EN]),
        )


class SettingsTests(unittest.TestCase):
    def test_legacy_preferences_survive_rename_and_save_to_new_location(self):
        with tempfile.TemporaryDirectory() as directory, mock.patch.dict(os.environ, {"APPDATA": directory}):
            legacy = os.path.join(directory, "JimengC4DUploader", "settings.json")
            os.makedirs(os.path.dirname(legacy))
            with open(legacy, "w", encoding="utf-8") as stream:
                json.dump({"language": "en"}, stream)
            self.assertEqual(settings.load(), {"language": "en"})
            settings.save({"language": "zh"})
            self.assertTrue(os.path.isfile(os.path.join(directory, "c4d-jimeng-uploader", "settings.json")))
            self.assertEqual(settings.load(), {"language": "zh"})
            with open(legacy, encoding="utf-8") as stream:
                self.assertEqual(json.load(stream), {"language": "en"})


class ProtocolTests(unittest.TestCase):
    def test_fallback_is_uploadable(self):
        config = protocol.fallback_config("offline")
        protocol.validate_export_protocol(config)
        self.assertEqual(protocol.prompt_for_export(config, ""), protocol.DEFAULT_PROMPT)
        protocol.validate_frame_range(config, 1, protocol.DEFAULT_MIN_FRAME_NUM)

    def test_custom_prompt_wins(self):
        self.assertEqual(protocol.prompt_for_export(protocol.fallback_config(), "  白模镜头推进  "), "白模镜头推进")


class BridgeTests(unittest.TestCase):
    def test_bridge_exposes_prompt_and_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "sample.mp4")
            # Minimal ISO base-media header. The bridge only streams the file;
            # codec validation happens before this layer in the plug-in.
            with open(path, "wb") as stream:
                stream.write(b"\x00\x00\x00\x18ftypisom\x00\x00\x02\x00isomiso2")
            result = bridge.start_local_bridge(path, "test prompt", ttl_seconds=10)
            resource_url = "http://127.0.0.1:{0}/resource_info?token={1}".format(result["port"], result["token"])
            with urllib.request.urlopen(resource_url, timeout=3) as response:
                payload = json.loads(response.read().decode("utf-8"))
            self.assertEqual(payload["prompt"], "test prompt")
            with urllib.request.urlopen(payload["file_url"], timeout=3) as response:
                self.assertEqual(response.read(8), b"\x00\x00\x00\x18ftyp")


class MediaTests(unittest.TestCase):
    def test_ffmpeg_override_prefers_new_name_and_accepts_legacy_name(self):
        with tempfile.TemporaryDirectory() as directory:
            current = os.path.join(directory, "current.exe")
            legacy = os.path.join(directory, "legacy.exe")
            for path in (current, legacy):
                with open(path, "wb"):
                    pass
            with mock.patch.dict(os.environ, {"C4D_JIMENG_UPLOADER_FFMPEG": current, "JIMENG_UPLOADER_FFMPEG": legacy}):
                self.assertEqual(media.ffmpeg_executable(), current)
                os.environ["C4D_JIMENG_UPLOADER_FFMPEG"] = ""
                self.assertEqual(media.ffmpeg_executable(), legacy)

    def test_h264_container_check_needs_no_ffmpeg(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "h264.mp4")
            with open(path, "wb") as stream:
                stream.write(b"\x00\x00\x00\x18ftypisom\x00\x00\x02\x00isomiso2avc1")
            original = media.ffmpeg_executable
            media.ffmpeg_executable = lambda: None
            try:
                info = media.inspect_h264_mp4(path)
            finally:
                media.ffmpeg_executable = original
            self.assertEqual(info["codec"], "h264")


if __name__ == "__main__":
    unittest.main()
