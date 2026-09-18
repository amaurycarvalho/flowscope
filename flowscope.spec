# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

import importlib.util
import sys
import os

if importlib.util.find_spec('litellm') is None:
    raise SystemExit(
        "litellm não instalado: rode 'pip install -e \".[llm]\"' antes de compilar."
    )

# O liteLLM é importado tardiamente pelo adaptador; coletamos submódulos e
# arquivos de dados (ex.: tabela de preços/contexto) para garantir o suporte a
# LLM em máquinas que rodam apenas o executável. Os assets do proxy web são
# dispensáveis e ficam de fora para não inflar o binário.
litellm_datas = [
    item
    for item in collect_data_files('litellm')
    if 'proxy/_experimental' not in item[0]
]
litellm_hiddenimports = collect_submodules('litellm')

if sys.platform == 'win32':
    icon_file = 'src/flowscope/icons/flowscope.ico'
elif sys.platform == 'darwin':
    icon_file = 'src/flowscope/icons/flowscope.icns'
else:
    icon_file = None

upx_enabled = sys.platform != 'darwin'
console_enabled = sys.platform != 'darwin'

a = Analysis(
    ['src/flowscope/presentation/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('src/flowscope/icons', 'icons'),
        *litellm_datas,
    ],
    hiddenimports=[
        'tkinter',
        'PIL',
        'PIL._tkinter_finder',
        'matplotlib',
        'matplotlib.figure',
        'matplotlib.backends.backend_tkagg',
        'mpl_toolkits',
        'mpl_toolkits.mplot3d',
        'ctypes',
        'pyxclip',
        'tkcalendar',
        'tkcalendar.entry',
        'tkcalendar.calendar_',
        'tkcalendar.tooltip',
        *litellm_hiddenimports,
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='flowscope',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=upx_enabled,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=console_enabled,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file,
)

if sys.platform == 'darwin':
    app = BUNDLE(
        exe,
        name='flowscope.app',
        icon=icon_file,
        bundle_identifier='com.github.amaurycarvalho.flowscope',
        info_plist={
            'CFBundleShortVersionString': '1.1.0',
            'CFBundleVersion': '1.1.0',
            'NSHighResolutionCapable': True,
        },
    )
