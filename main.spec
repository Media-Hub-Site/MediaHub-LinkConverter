# -*- mode: python ; coding: utf-8 -*-
import sys
import os

sys.path.insert(0, os.path.abspath('.'))

from PyInstaller.utils.hooks import collect_submodules

hidden_imports = [
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.QtWidgets',
    'yt_dlp',
    'imageio_ffmpeg',
]
hidden_imports += collect_submodules('apps.link_converter')
hidden_imports += collect_submodules('core')
hidden_imports += collect_submodules('yt_dlp')

datas = [
    ('assets', 'assets'),
]

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='MediaHub-LinkConverter',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon='assets/hub/Media-Hub.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='MediaHub-LinkConverter',
)
