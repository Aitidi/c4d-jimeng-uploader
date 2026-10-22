"""Cinema 4D command plug-in registration."""

from __future__ import annotations

import c4d
from c4d import plugins

from .constants import PLUGIN_HELP, PLUGIN_ID, PLUGIN_NAME
from .dialog import UploaderDialog


_DIALOG = None
_REGISTERED = False


class C4DJimengUploaderCommand(plugins.CommandData):
    def Execute(self, _doc):
        global _DIALOG
        if _DIALOG is None:
            _DIALOG = UploaderDialog()
        return _DIALOG.Open(c4d.DLG_TYPE_ASYNC, PLUGIN_ID, defaultw=680, defaulth=590)

    def RestoreLayout(self, secret):
        global _DIALOG
        if _DIALOG is None:
            _DIALOG = UploaderDialog()
        return _DIALOG.Restore(PLUGIN_ID, secret)


def register():
    global _REGISTERED
    if _REGISTERED:
        return True
    _REGISTERED = plugins.RegisterCommandPlugin(
        id=PLUGIN_ID,
        str=PLUGIN_NAME,
        info=0,
        icon=None,
        help=PLUGIN_HELP,
        dat=C4DJimengUploaderCommand(),
    )
    return _REGISTERED
