# -*- mode: python ; coding: utf-8 -*-

import os

block_cipher = None

a = Analysis(
    ['faceonstudio.py'],
    pathex=[os.getcwd()],
    binaries=[],
    datas=[],
    hiddenimports=['onnxruntime.capi._pybind_state'],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# --- Configuration for a ONE-FILE build (your original request) ---
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='FaceOn Studio',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    runtime_tmpdir=None,
    icon='icon.ico'
)

# --- UNCOMMENT BELOW FOR A ONE-FOLDER build (for debugging) ---
# coll = COLLECT(
#     exe,
#     a.binaries,
#     a.zipfiles,
#     a.datas,
#     strip=False,
#     upx=True,
#     upx_exclude=[],
#     name='FaceOn Studio',
# )