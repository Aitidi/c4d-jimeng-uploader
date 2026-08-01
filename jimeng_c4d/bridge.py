"""Temporary, token-protected localhost bridge consumed by Jimeng Web."""

from __future__ import annotations

import base64
import http.server
import json
import os
import secrets
import shutil
import threading
import time
import urllib.parse


DEFAULT_TARGET_URL = "https://jimeng.jianying.com/ai-tool/home"
DEFAULT_TTL_SECONDS = 30 * 60
DEFAULT_CLOSE_AFTER_DOWNLOAD_SECONDS = 60
_BRIDGES = {}


class UploadError(RuntimeError):
    pass


def _base64_url(value):
    return base64.urlsafe_b64encode(value.encode("utf-8")).decode("ascii").rstrip("=")


def _allowed_origin(origin):
    if not origin:
        return False
    try:
        parsed = urllib.parse.urlparse(origin)
    except ValueError:
        return False
    host = parsed.hostname or ""
    if parsed.scheme == "https" and (host == "jimeng.jianying.com" or host.endswith(".jianying.com") or host == "dreamina.capcut.com" or host.endswith(".capcut.com")):
        return True
    return parsed.scheme in ("http", "https") and host in ("localhost", "127.0.0.1", "::1")


def _content_disposition(path):
    name = os.path.basename(path).replace("\r", "_").replace("\n", "_")
    fallback = "".join(char if 0x20 <= ord(char) <= 0x7E and char != '"' else "_" for char in name)
    return "inline; filename=\"{0}\"; filename*=UTF-8''{1}".format(fallback, urllib.parse.quote(name))


def _redirect_url(target_url, resource_info_url):
    parsed = urllib.parse.urlparse(target_url or DEFAULT_TARGET_URL)
    path = "/ai-tool/home" if parsed.path.rstrip("/") == "/ai-tool" else parsed.path
    query = [(key, value) for key, value in urllib.parse.parse_qsl(parsed.query, keep_blank_values=True) if key not in ("channel", "thirdparty_id")]
    query.extend((("channel", "blender"), ("thirdparty_id", _base64_url(resource_info_url))))
    return urllib.parse.urlunparse(parsed._replace(path=path, query=urllib.parse.urlencode(query)))


def start_local_bridge(video_path, prompt, target_url=DEFAULT_TARGET_URL, ttl_seconds=DEFAULT_TTL_SECONDS):
    video_path = os.path.abspath(video_path)
    if not os.path.isfile(video_path):
        raise UploadError("视频文件不存在：{0}".format(video_path))
    if os.path.splitext(video_path)[1].lower() != ".mp4":
        raise UploadError("本机桥接仅接受 MP4 文件。")

    token = secrets.token_urlsafe(24)
    expires_at = time.time() + float(ttl_seconds)
    prompt_text = prompt or ""

    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, _format, *_args):
            return

        def _cors(self):
            origin = self.headers.get("Origin", "")
            if _allowed_origin(origin):
                self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
            self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Access-Control-Allow-Private-Network", "true")

        def _json(self, code, payload):
            body = json.dumps(payload).encode("utf-8")
            self.send_response(code)
            self._cors()
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_OPTIONS(self):
            self.send_response(204)
            self._cors()
            self.end_headers()

        def do_GET(self):
            parsed = urllib.parse.urlparse(self.path or "")
            received_token = (urllib.parse.parse_qs(parsed.query).get("token") or [""])[0]
            if received_token != token:
                self._json(403, {"status": "failed", "code": "INVALID_TOKEN"})
                return
            if time.time() > expires_at:
                self._json(410, {"status": "failed", "code": "TOKEN_EXPIRED"})
                schedule_shutdown(0)
                return
            if parsed.path in ("/resouce_info", "/resource_info"):
                self._json(200, {"file_url": "http://127.0.0.1:{0}/file?token={1}".format(server.server_port, urllib.parse.quote(token)), "prompt": prompt_text})
                return
            if parsed.path != "/file":
                self._json(404, {"status": "failed", "code": "NOT_FOUND"})
                return
            if not os.path.isfile(video_path):
                self._json(404, {"status": "failed", "code": "FILE_NOT_FOUND"})
                return
            self.send_response(200)
            self._cors()
            self.send_header("Content-Type", "video/mp4")
            self.send_header("Content-Length", str(os.path.getsize(video_path)))
            self.send_header("Content-Disposition", _content_disposition(video_path))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            with open(video_path, "rb") as stream:
                shutil.copyfileobj(stream, self.wfile)
            schedule_shutdown(DEFAULT_CLOSE_AFTER_DOWNLOAD_SECONDS)

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    timer_ref = {"timer": None}

    def schedule_shutdown(delay):
        previous = timer_ref.get("timer")
        if previous:
            previous.cancel()

        def close_server():
            try:
                server.shutdown()
            except Exception:
                pass
            try:
                server.server_close()
            except Exception:
                pass
            _BRIDGES.pop(token, None)

        timer = threading.Timer(max(0.0, float(delay)), close_server)
        timer.daemon = True
        timer_ref["timer"] = timer
        timer.start()

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    schedule_shutdown(ttl_seconds)
    _BRIDGES[token] = server

    resource_info_url = "http://127.0.0.1:{0}/resouce_info?token={1}".format(server.server_port, urllib.parse.quote(token))
    return {
        "status": "ready",
        "token": token,
        "port": int(server.server_port),
        "video": video_path,
        "expires_at": int(expires_at * 1000),
        "redirect_url": _redirect_url(target_url, resource_info_url),
    }


def bridge_is_alive(token, expires_at_ms):
    return bool(token and token in _BRIDGES and int(time.time() * 1000) < int(expires_at_ms or 0))
