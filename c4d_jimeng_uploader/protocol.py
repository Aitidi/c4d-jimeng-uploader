"""Jimeng DCC protocol configuration client shared by the C4D plug-in."""

from __future__ import annotations

import http.client
import json
import os
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse


DCC_CONFIG_PATH = "/mweb/v1/get_dcc_protocol_config"
DEFAULT_CONFIG_URL = "https://jimeng.jianying.com" + DCC_CONFIG_PATH
DEFAULT_CONFIG_HEADERS = {
    "content-type": "application/json",
    "x-use-ppe": "1",
    "x-tt-env": "ppe_dreamina_support_blender",
}
DEFAULT_CONFIG_QUERY = {"need_install_packages": "false"}

DEFAULT_PROMPT = "A cinematic high quality video"
DEFAULT_FILE_SIZE = 200 * 1024 * 1024
DEFAULT_FPS = 24
DEFAULT_DURATION = 30
DEFAULT_MIN_FRAME_NUM = 44
DEFAULT_MAX_FRAME_NUM = DEFAULT_DURATION * DEFAULT_FPS
DEFAULT_RESOLUTION_KEY = "720p"

DEFAULT_RESOLUTIONS = (
    {"key": "360p", "label": "360P", "short_edge": 360},
    {"key": "480p", "label": "480P", "short_edge": 480},
    {"key": "720p", "label": "720P", "short_edge": 720},
    {"key": "1080p", "label": "1080P", "short_edge": 1080},
    {"key": "origin", "label": "Origin", "origin": True, "short_edge": 0},
)


class DccConfigError(RuntimeError):
    """The protocol data is unusable for a Jimeng upload."""


def _positive_int(value, fallback):
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return fallback
    return parsed if parsed > 0 else fallback


def normalize_resolution_key(value, fallback=DEFAULT_RESOLUTION_KEY):
    key = str(value or "").strip().lower()
    if key in ("360", "480", "720", "1080"):
        key += "p"
    if key in {item["key"] for item in DEFAULT_RESOLUTIONS}:
        return key
    return fallback


def fallback_config(reason=""):
    return {
        "video_protocol": {
            "fps": DEFAULT_FPS,
            "container_format": "mp4",
            "codec": "h264",
            "file_size": DEFAULT_FILE_SIZE,
            "duration": DEFAULT_DURATION,
            "min_frame_num": DEFAULT_MIN_FRAME_NUM,
            "max_frame_num": DEFAULT_MAX_FRAME_NUM,
            "resolution_list": [dict(item) for item in DEFAULT_RESOLUTIONS],
        },
        "default_prompt": DEFAULT_PROMPT,
        "source": "fallback",
        "warning": reason,
    }


def normalize_config(data, source="remote", warning=""):
    data = data if isinstance(data, dict) else {}
    video = data.get("video_protocol") if isinstance(data.get("video_protocol"), dict) else {}
    return {
        "video_protocol": {
            "fps": _positive_int(video.get("fps"), DEFAULT_FPS),
            "container_format": str(video.get("container_format") or "mp4").lower(),
            "codec": str(video.get("codec") or "h264").lower(),
            "file_size": _positive_int(video.get("file_size"), DEFAULT_FILE_SIZE),
            "duration": _positive_int(video.get("duration"), DEFAULT_DURATION),
            "min_frame_num": _positive_int(video.get("min_frame_num"), DEFAULT_MIN_FRAME_NUM),
            "max_frame_num": _positive_int(video.get("max_frame_num"), DEFAULT_MAX_FRAME_NUM),
            "resolution_list": [dict(item) for item in DEFAULT_RESOLUTIONS],
        },
        "default_prompt": str(data.get("default_prompt") or DEFAULT_PROMPT),
        "source": source,
        "warning": warning,
    }


def video_protocol(config):
    return (config or {}).get("video_protocol") or fallback_config()["video_protocol"]


def prompt_for_export(config, prompt):
    return str(prompt or "").strip() or str((config or {}).get("default_prompt") or DEFAULT_PROMPT)


def validate_export_protocol(config):
    protocol = video_protocol(config)
    container = str(protocol.get("container_format") or "").lower()
    codec = str(protocol.get("codec") or "").lower()
    if container != "mp4":
        raise DccConfigError("即梦当前仅支持 MP4 输出。")
    if codec not in {"h264", "h.264", "avc", "avc1", "libx264"}:
        raise DccConfigError("即梦当前仅支持 H.264 编码。")


def validate_frame_range(config, start_frame, end_frame):
    protocol = video_protocol(config)
    start, end = int(start_frame), int(end_frame)
    if start > end:
        raise DccConfigError("起始帧不能大于结束帧。")
    count = end - start + 1
    minimum = _positive_int(protocol.get("min_frame_num"), DEFAULT_MIN_FRAME_NUM)
    maximum = _positive_int(protocol.get("max_frame_num"), DEFAULT_MAX_FRAME_NUM)
    if count < minimum:
        raise DccConfigError("帧范围过短：{0} 帧，至少需要 {1} 帧。".format(count, minimum))
    if maximum and count > maximum:
        raise DccConfigError("帧范围过长：{0} 帧，最多支持 {1} 帧。".format(count, maximum))


def validate_file_size(path, config):
    limit = _positive_int(video_protocol(config).get("file_size"), DEFAULT_FILE_SIZE)
    size = os.path.getsize(path)
    if size > limit:
        raise DccConfigError("视频过大：{0}，上限为 {1}。".format(format_bytes(size), format_bytes(limit)))


def format_bytes(size):
    value = float(size)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024 or unit == "GB":
            return "{0}B".format(int(value)) if unit == "B" else "{0:.1f}{1}".format(value, unit)
        value /= 1024
    return "{0}B".format(size)


def _with_default_query(url):
    parsed = urlparse(url)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query.update({key: query.get(key, value) for key, value in DEFAULT_CONFIG_QUERY.items()})
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, urlencode(query), parsed.fragment))


def _candidate_urls(target_url=None):
    urls = []
    env_url = os.environ.get("JIMENG_DCC_CONFIG_URL", "").strip()
    if env_url:
        urls.append(env_url)
    if target_url:
        parsed = urlparse(target_url)
        if parsed.scheme and parsed.netloc:
            urls.append("{0}://{1}{2}".format(parsed.scheme, parsed.netloc, DCC_CONFIG_PATH))
    urls.append(DEFAULT_CONFIG_URL)
    result = []
    for url in urls:
        value = _with_default_query(url)
        if value not in result:
            result.append(value)
    return result


def _post_json(url, timeout):
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise DccConfigError("无效的 DCC 配置地址：{0}".format(url))
    path = parsed.path or "/"
    if parsed.query:
        path += "?" + parsed.query
    connection_type = http.client.HTTPSConnection if parsed.scheme == "https" else http.client.HTTPConnection
    connection = connection_type(parsed.netloc, timeout=timeout)
    try:
        connection.request("POST", path, body=b"{}", headers=DEFAULT_CONFIG_HEADERS)
        response = connection.getresponse()
        body = response.read().decode("utf-8", "replace")
        if not 200 <= response.status < 300:
            raise DccConfigError("HTTP {0}: {1}".format(response.status, body[:200]))
        return body
    finally:
        connection.close()


def fetch_dcc_protocol_config(target_url=None, timeout=5):
    errors = []
    for url in _candidate_urls(target_url):
        try:
            response = json.loads(_post_json(url, timeout))
            if isinstance(response, dict) and str(response.get("ret", "0")) != "0":
                raise DccConfigError("DCC 返回错误：{0}".format(response.get("errmsg", "未知错误")))
            data = response.get("data") if isinstance(response, dict) else None
            if not isinstance(data, dict):
                raise DccConfigError("DCC 配置响应缺少 data。")
            return normalize_config(data, source=url)
        except Exception as exc:
            errors.append("{0}: {1}".format(url, exc))
    return fallback_config("; ".join(errors))
