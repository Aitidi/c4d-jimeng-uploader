"""Small JSON preference store kept outside Cinema 4D scene files."""

from __future__ import annotations

import json
import os

from .constants import PLUGIN_NAME


def _config_dir():
    root = os.environ.get("APPDATA") or os.path.expanduser("~")
    return os.path.join(root, PLUGIN_NAME)


def config_path():
    return os.path.join(_config_dir(), "settings.json")


def default_output_dir():
    return os.path.join(_config_dir(), "renders")


def load():
    # Read existing preferences until they are next saved under the new name.
    path = config_path()
    if not os.path.exists(path):
        root = os.path.dirname(_config_dir())
        path = os.path.join(root, "JimengC4DUploader", "settings.json")
    try:
        with open(path, "r", encoding="utf-8") as stream:
            value = json.load(stream)
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError, TypeError):
        return {}


def save(value):
    directory = _config_dir()
    os.makedirs(directory, exist_ok=True)
    path = config_path()
    temporary = path + ".tmp"
    with open(temporary, "w", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
    os.replace(temporary, path)
