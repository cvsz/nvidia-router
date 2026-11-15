# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['../../zcloud-gui.py'],
    pathex=[],
    binaries=[],
    datas=[('/mnt/zdata/nvidia/models.json', '.'), ('/mnt/zdata/nvidia/provider.json', '.'), ('/mnt/zdata/nvidia/nvidia.ico', '.'), ('/mnt/zdata/nvidia/nvidia.png', '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='zcloud-enterprise',
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
    icon=['nvidia.ico'],
)
