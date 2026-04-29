# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
import sys

from PyInstaller.utils.hooks import collect_submodules

project_dir = Path(SPECPATH)
base_python_dir = Path(sys.base_prefix)

datas = [
    (str(project_dir / "logo_pdf_app.png"), "."),
]

binaries = [
    (str(base_python_dir / "DLLs" / "tcl86t.dll"), "."),
    (str(base_python_dir / "DLLs" / "tk86t.dll"), "."),
]

a = Analysis(
    ["main.py"],
    pathex=[str(project_dir)],
    binaries=binaries,
    datas=datas,
    hiddenimports=[
        "tkinter",
        "tkinter.filedialog",
        "tkinter.messagebox",
        "tkinter.ttk",
        "pypdf",
        *collect_submodules("pypdf"),
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
a.datas += Tree(str(base_python_dir / "tcl" / "tcl8.6"), prefix="tcl/tcl8.6")
a.datas += Tree(str(base_python_dir / "tcl" / "tk8.6"), prefix="tcl/tk8.6")
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="PDFCombine",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(project_dir / "app_icon.ico"),
)
