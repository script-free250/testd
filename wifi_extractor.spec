# wifi_extractor.spec
# =====================================================================
# PyInstaller specification file for WiFi Credential Extractor
# This file controls exactly how the .exe is built:
#   - Single-file bundle (onefile)
#   - No console window (windowed)
#   - Custom icon support
#   - All tkinter dependencies included automatically
# =====================================================================

import sys
from PyInstaller.building.build_main import Analysis, PYZ, EXE

# ── Collect all data/binary dependencies ──
block_cipher = None

a = Analysis(
    # Main script entry point
    scripts=['wifi_extractor.py'],

    # Extra paths to search for imports (empty = use sys.path)
    pathex=[],

    # Binary files to include (e.g., DLLs) — PyInstaller auto-detects most
    binaries=[],

    # Non-Python data files to bundle: list of (source, dest_folder) tuples
    datas=[],

    # Additional hidden imports that PyInstaller's static analysis might miss
    hiddenimports=[
        'tkinter',
        'tkinter.ttk',
        'tkinter.messagebox',
        'tkinter.filedialog',
        '_tkinter',
        'csv',
        'json',
        'subprocess',
        'datetime',
    ],

    # Hook directories for additional PyInstaller hooks (none needed here)
    hookspath=[],

    # Runtime hooks run before any user code
    runtime_hooks=[],

    # Modules to explicitly exclude to reduce bundle size
    excludes=[
        'matplotlib',
        'numpy',
        'pandas',
        'PIL',
        'scipy',
        'PyQt5',
        'PySide2',
        'wx',
    ],

    # Do not encrypt bytecode
    cipher=block_cipher,

    # Allow noarchive mode (False = bundle everything into the .exe)
    noarchive=False,
)

# ── Create the Python archive (bytecode) ──
pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

# ── Build the final .exe ──
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,

    # Output filename (without extension — PyInstaller adds .exe on Windows)
    name='WiFiExtractor',

    # Show a debug console window? False = clean GUI only
    console=False,

    # Strip debug symbols to reduce size
    strip=False,

    # Use UPX compression if available (reduces .exe size ~30-50%)
    upx=True,
    upx_exclude=[],

    # Runtime temp directory name (used in onefile mode)
    runtime_tmpdir=None,

    # Set the .exe icon — file must exist; CI workflow handles this
    # icon='icon.ico',   # Uncomment if you provide an icon.ico file

    # Bundle everything into a single .exe file
    onefile=True,

    # Windows-specific version info (optional)
    # version='version_info.txt',  # Uncomment to embed version metadata
)
