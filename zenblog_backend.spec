# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['zenblog_backend.py'],
    pathex=[],
    binaries=[],
    datas=[('data', 'data'), ('images', 'images'), ('index.html', '.'), ('logo.png', '.')],
    hiddenimports=['uvicorn', 'uvicorn.logging', 'uvicorn.loops', 'uvicorn.loops.auto', 'uvicorn.protocols', 'uvicorn.protocols.http', 'uvicorn.protocols.http.auto', 'uvicorn.protocols.websocket', 'uvicorn.protocols.websocket.auto', 'fastapi', 'pydantic', 'starlette', 'starlette.routing', 'starlette.middleware', 'starlette.middleware.cors', 'starlette.staticfiles', 'starlette.responses', 'requests'],
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
    name='zenblog_backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
