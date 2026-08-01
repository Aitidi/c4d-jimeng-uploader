"""Cinema 4D entry point for the Jimeng white-model uploader."""

from __future__ import annotations

import os
import sys


PLUGIN_ROOT = os.path.dirname(os.path.abspath(__file__))
if PLUGIN_ROOT not in sys.path:
    sys.path.insert(0, PLUGIN_ROOT)

from jimeng_c4d.plugin import register


register()
