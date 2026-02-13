# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:\\Users\\lucas.LUCAS\\sistema-de-questoes\\src\\main.py'],
    pathex=[],
    binaries=[],
    datas=[('config.ini', '.'), ('imagens/logos', 'imagens/logos'), ('templates/latex', 'templates/latex'), ('.env', '.')],
    hiddenimports=['PyQt6.QtWebEngineWidgets', 'pymongo', 'dns.resolver', 'sqlalchemy.dialects.sqlite'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['backend', 'tests', 'pytest', 'unittest'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='OharaBank',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['C:\\Users\\lucas.LUCAS\\sistema-de-questoes\\imagens\\logos\\logoapp.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='OharaBank',
)
