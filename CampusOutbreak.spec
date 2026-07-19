# Campus Outbreak - PyInstaller configuration

from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT
from PyInstaller.utils.hooks import collect_dynamic_libs


# ---------------------------------------------------------
# DATA FOLDERS
# ---------------------------------------------------------

datas = [
    ("ending", "ending"),
    ("intro", "intro"),
    ("sounds", "sounds"),
]


# ---------------------------------------------------------
# REQUIRED DLLS
# ---------------------------------------------------------

binaries = []

# Collect every native DLL required by pygame-ce
binaries += collect_dynamic_libs("pygame")


# ---------------------------------------------------------
# PYTHON MODULES
# ---------------------------------------------------------

hiddenimports = [
    "vlc",
]


# ---------------------------------------------------------
# ANALYSIS
# ---------------------------------------------------------

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


# ---------------------------------------------------------
# PYZ
# ---------------------------------------------------------

pyz = PYZ(a.pure)


# ---------------------------------------------------------
# EXECUTABLE
# ---------------------------------------------------------

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="CampusOutbreak",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)


# ---------------------------------------------------------
# COLLECT
# ---------------------------------------------------------

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    name="CampusOutbreak",
)