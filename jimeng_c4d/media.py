"""MP4 validation without any transcoding."""

from __future__ import annotations

import os
import shutil
import subprocess


class VideoValidationError(RuntimeError):
    pass


def _ffmpeg_candidates():
    env_path = os.environ.get("JIMENG_UPLOADER_FFMPEG", "").strip()
    if env_path:
        yield env_path
    found = shutil.which("ffmpeg")
    if found:
        yield found
    package_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    workspace_root = os.path.dirname(package_root)
    bundled = os.path.join(workspace_root, "jimeng_blender_uploader", "runtime", "ffmpeg", "windows-x86_64", "ffmpeg.exe")
    if os.path.isfile(bundled):
        yield bundled


def ffmpeg_executable():
    for candidate in _ffmpeg_candidates():
        if os.path.isfile(candidate):
            return candidate
    return None


def _has_mp4_signature(path):
    with open(path, "rb") as stream:
        header = stream.read(32)
    return len(header) >= 8 and header[4:8] == b"ftyp"


def _has_h264_sample_entry(path):
    """Detect AVC sample entries without decoding or rewriting the movie."""
    markers = (b"avc1", b"avc3")
    with open(path, "rb") as stream:
        previous = b""
        while True:
            chunk = stream.read(1024 * 1024)
            if not chunk:
                return False
            data = previous + chunk
            if any(marker in data for marker in markers):
                return True
            previous = data[-3:]


def inspect_h264_mp4(path, require_probe=False):
    path = os.path.abspath(path)
    if not os.path.isfile(path):
        raise VideoValidationError("视频文件不存在。")
    if os.path.splitext(path)[1].lower() != ".mp4":
        raise VideoValidationError("仅支持 MP4 文件。")
    if os.path.getsize(path) <= 0 or not _has_mp4_signature(path):
        raise VideoValidationError("文件不是有效的 MP4 容器。")

    if not _has_h264_sample_entry(path):
        raise VideoValidationError("MP4 不包含 H.264/AVC 视频流。请在 C4D 的 Save > MP4 > Options 中选择 H.264。")

    ffmpeg = ffmpeg_executable()
    if not ffmpeg:
        if require_probe:
            raise VideoValidationError("无法执行完整编码检查：未找到 ffmpeg。")
        return {"codec": "h264", "pixel_format": "unverified", "probe": "container"}

    result = subprocess.run([ffmpeg, "-hide_banner", "-i", path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace", check=False)
    output = result.stdout.lower()
    if "video: h264" not in output:
        raise VideoValidationError("MP4 不是 H.264 视频。请在 C4D 的 Save > MP4 > Options 中选择 H.264。")
    if "yuv420" not in output:
        raise VideoValidationError("H.264 视频必须使用 yuv420 像素格式。请在 C4D 的 MP4 设置中选择 8 Bit/Channel。")
    return {"codec": "h264", "pixel_format": "yuv420p", "probe": ffmpeg}
