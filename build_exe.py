"""
WinLink Production Build Script
Creates standalone executable using PyInstaller
"""
import os
import sys
import shutil
import subprocess

def clean_build():
    """Clean previous build artifacts"""
    print("Cleaning previous builds...")
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"  Removed {dir_name}/")
    
    for file in ['WinLink.spec']:
        if os.path.exists(file):
            os.remove(file)
            print(f"  Removed {file}")

def check_pyinstaller():
    """Check if PyInstaller is installed"""
    try:
        import PyInstaller
        print("PyInstaller found!")
        return True
    except ImportError:
        print("PyInstaller not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        return True

def create_spec_file():
    """Create PyInstaller spec file"""
    # Create a spec that collects assets, PyQt5 plugins (platforms & imageformats),
    # and includes hiddenimports for matplotlib and numpy. UPX is disabled by default
    # because UPX may not be installed on the build machine.
    # Optionally bundle VLC native files if available on the build machine
    BUNDLE_VLC = True

    def find_vlc():
        # Common Windows VLC locations
        candidates = [
            r"C:\Program Files\VideoLAN\VLC",
            r"C:\Program Files (x86)\VideoLAN\VLC",
        ]
        # Also check environment variable (if user set VLC_PATH)
        env_vlc = os.environ.get('VLC_PATH')
        if env_vlc:
            candidates.insert(0, env_vlc)

        for p in candidates:
            if os.path.isdir(p):
                return p
        return None

    vlc_path = find_vlc() if BUNDLE_VLC else None
    if vlc_path:
        print(f"Found VLC installation at: {vlc_path} — bundling into package")
    else:
        if BUNDLE_VLC:
            print("VLC not found on build machine — skipping VLC bundling")

    spec_content = f"""# -*- mode: python ; coding: utf-8 -*-

import os
import PyQt5
from PyInstaller.utils.hooks import collect_submodules, collect_data_files, Tree

block_cipher = None

# Location of PyQt5 plugins (platforms, imageformats, etc.)
pyqt_plugin_dir = os.path.join(PyQt5.__path__[0], 'Qt', 'plugins')

datas = [
    ('README.md', '.'),
    ('requirements.txt', '.'),
]

# Include assets and PyQt5 plugins
datas = datas + Tree('assets', prefix='assets') + Tree(pyqt_plugin_dir, prefix=os.path.join('PyQt5', 'Qt', 'plugins'))

# Optionally include VLC native files (copy entire folder under 'vlc/')
{ 'vlc_tree = "datas = datas + Tree(%r, prefix=\'vlc\')" % vlc_path if vlc_path else '\n' }

# Hidden imports to help PyInstaller collect dynamic backends
hiddenimports = [
    'PyQt5.QtCore',
    'PyQt5.QtGui',
    'PyQt5.QtWidgets',
    'matplotlib.backends.backend_qt5agg',
    'matplotlib.backends.backend_agg',
    'numpy',
    'vlc',
]

a = Analysis(
    ['launch_enhanced.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='WinLink',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/WinLink_logo.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='WinLink',
)
"""
    
    with open('WinLink.spec', 'w') as f:
        f.write(spec_content)
    print("Created WinLink.spec file")

def build_executable():
    """Build the executable using PyInstaller"""
    print("\nBuilding executable...")
    print("This may take several minutes...\n")
    
    try:
        # Use python -m PyInstaller instead of direct pyinstaller command
        subprocess.check_call([
            sys.executable,
            '-m',
            'PyInstaller',
            '--clean',
            'WinLink.spec'
        ])
        print("\n✓ Build completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Build failed: {e}")
        return False
    except Exception as e:
        print(f"\n✗ Build error: {e}")
        print("\nTrying alternative method...")
        try:
            # Fallback: try direct import and run
            from PyInstaller import __main__ as pyi_main
            pyi_main.run(['--clean', 'WinLink.spec'])
            print("\n✓ Build completed successfully!")
            return True
        except Exception as e2:
            print(f"\n✗ Alternative method also failed: {e2}")
            return False

def create_distribution_package():
    """Create final distribution package"""
    print("\nCreating distribution package...")
    
    dist_dir = 'dist/WinLink'
    if not os.path.exists(dist_dir):
        print("✗ Distribution directory not found!")
        return False
    
    # Create production folder
    prod_dir = 'WinLink_Production'
    if os.path.exists(prod_dir):
        shutil.rmtree(prod_dir)
    os.makedirs(prod_dir)
    
    # Copy executable and dependencies
    shutil.copytree(dist_dir, os.path.join(prod_dir, 'WinLink'))
    
    # Create necessary directories
    os.makedirs(os.path.join(prod_dir, 'WinLink', 'logs'), exist_ok=True)
    os.makedirs(os.path.join(prod_dir, 'WinLink', 'data'), exist_ok=True)
    os.makedirs(os.path.join(prod_dir, 'WinLink', 'secrets'), exist_ok=True)
    os.makedirs(os.path.join(prod_dir, 'WinLink', 'ssl'), exist_ok=True)
    
    # Copy batch files for convenience
    batch_files = ['setup_firewall.bat']
    for bat in batch_files:
        if os.path.exists(bat):
            shutil.copy(bat, os.path.join(prod_dir, bat))
    
    # Create launcher batch file
    launcher_content = """@echo off
title WinLink - Distributed Computing Platform

cd WinLink
start WinLink.exe
"""
    with open(os.path.join(prod_dir, 'Start_WinLink.bat'), 'w') as f:
        f.write(launcher_content)
    
    # Create README for distribution
    readme_content = """WinLink - Distributed Computing Platform
==========================================

INSTALLATION:
1. Extract this folder to your desired location
2. Run setup_firewall.bat as Administrator (if networking is needed)
3. Double-click Start_WinLink.bat to launch the application

FIRST RUN:
- On first launch, the application will generate necessary security certificates
- Choose your role: Master (to distribute tasks) or Worker (to execute tasks)

SYSTEM REQUIREMENTS:
- Windows 10/11 (64-bit)
- 4GB RAM minimum (8GB recommended)
- Network connection (for distributed computing)

FIREWALL CONFIGURATION:
- Master PC: No special configuration needed
- Worker PC: Run setup_firewall.bat as Administrator

SUPPORT:
For issues or questions, refer to the full documentation or contact support.

Version: 2.0
"""
    with open(os.path.join(prod_dir, 'README.txt'), 'w') as f:
        f.write(readme_content)
    
    print(f"✓ Production package created: {prod_dir}/")
    print(f"\nPackage contents:")
    print(f"  - WinLink/ (executable and dependencies)")
    print(f"  - Start_WinLink.bat (launcher)")
    print(f"  - setup_firewall.bat (firewall configuration)")
    print(f"  - README.txt (user guide)")
    
    return True

def main():
    print("=" * 60)
    print("WinLink Production Build Script")
    print("=" * 60)
    print()
    
    # Step 1: Clean previous builds
    clean_build()
    print()
    
    # Step 2: Check PyInstaller
    if not check_pyinstaller():
        print("✗ Failed to install PyInstaller")
        return False
    print()
    
    # Step 3: Create spec file
    create_spec_file()
    print()
    
    # Step 4: Build executable
    if not build_executable():
        return False
    
    # Step 5: Create distribution package
    if not create_distribution_package():
        return False
    
    print("\n" + "=" * 60)
    print("BUILD SUCCESSFUL!")
    print("=" * 60)
    print("\nYour production-ready package is in: WinLink_Production/")
    print("\nTo distribute:")
    print("1. Zip the WinLink_Production folder")
    print("2. Share with end users")
    print("3. Users should extract and run Start_WinLink.bat")
    print("\nNote: First launch may take longer as it initializes security.")
    print()
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        input("\nPress Enter to exit...")
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nBuild cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")
        sys.exit(1)
