# =========================================================
# CAMPUS OUTBREAK
# PyInstaller - Single EXE Configuration
# =========================================================

import os

from PyInstaller.building.build_main import Analysis, PYZ, EXE
from PyInstaller.utils.hooks import collect_dynamic_libs


# =========================================================
# PATHS
# =========================================================

VLC_PATH = r"C:\Program Files\VideoLAN\VLC"

VLC_LIBVLC = os.path.join(VLC_PATH, "libvlc.dll")
VLC_LIBVLCCORE = os.path.join(VLC_PATH, "libvlccore.dll")
VLC_PLUGINS = os.path.join(VLC_PATH, "plugins")


# =========================================================
# VALIDATE VLC INSTALLATION
# =========================================================

if not os.path.isfile(VLC_LIBVLC):
    raise FileNotFoundError(
        f"VLC libvlc.dll not found:\n{VLC_LIBVLC}\n\n"
        "Install VLC 64-bit or change VLC_PATH in this spec file."
    )

if not os.path.isfile(VLC_LIBVLCCORE):
    raise FileNotFoundError(
        f"VLC libvlccore.dll not found:\n{VLC_LIBVLCCORE}\n\n"
        "Check your VLC installation."
    )

if not os.path.isdir(VLC_PLUGINS):
    raise FileNotFoundError(
        f"VLC plugins folder not found:\n{VLC_PLUGINS}\n\n"
        "Check your VLC installation."
    )


# =========================================================
# GAME DATA
# =========================================================

datas = [
    ("ending", "ending"),
    ("intro", "intro"),
    ("sounds", "sounds"),
]


# =========================================================
# PYGAME DLLS
# =========================================================

binaries = collect_dynamic_libs("pygame")


# =========================================================
# VLC RUNTIME
# =========================================================
#
# VLC needs:
#
#   libvlc.dll
#   libvlccore.dll
#   plugins\
#
# Everything is extracted beside the executable's temporary
# PyInstaller runtime directory when --onefile is used.
# =========================================================

binaries += [
    (
        VLC_LIBVLC,
        "."
    ),
    (
        VLC_LIBVLCCORE,
        "."
    ),
]


# ---------------------------------------------------------
# VLC PLUGINS
# ---------------------------------------------------------

datas += [
    (
        VLC_PLUGINS,
        "plugins"
    ),
]


# =========================================================
# PYTHON MODULES
# =========================================================

hiddenimports = [
    "vlc",
]


# =========================================================
# ANALYSIS
# =========================================================

a = Analysis(
    ["main.py"],

    pathex=[],

    binaries=binaries,

    datas=datas,

    hiddenimports=hiddenimports,

    hookspath=[],

    hooksconfig={},

    runtime_hooks=[],

    excludes=[],

    noarchive=False,
)


# =========================================================
# PYZ
# =========================================================

pyz = PYZ(
    a.pure
)


# =========================================================
# SINGLE EXE
# =========================================================

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],

    name="CampusOutbreak",

    debug=False,

    bootloader_ignore_signals=False,

    strip=False,

    # Do not use UPX.
    # This reduces the possibility of antivirus false positives
    # and avoids compression problems with native DLLs.
    upx=False,

    console=False,
)