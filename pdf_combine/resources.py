from __future__ import annotations

import os
from pathlib import Path
import sys


def project_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent


def resource_path(name: str) -> Path:
    return project_root() / name


def configure_tk_environment():
    if not getattr(sys, "frozen", False):
        return

    tcl_path = resource_path("tcl/tcl8.6")
    tk_path = resource_path("tcl/tk8.6")

    if tcl_path.exists():
        os.environ.setdefault("TCL_LIBRARY", str(tcl_path))
    if tk_path.exists():
        os.environ.setdefault("TK_LIBRARY", str(tk_path))
