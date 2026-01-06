"""
WinLink Production Build Script
Creates standalone executable using PyInstaller
"""
import os
import sys
import shutil
import subprocess
import textwrap

import datetime

def clean_build():
    """Clean previous builds and spec file"""
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
    BUNDLE_VLC = False

    
    vlc_tree = "\n"

    # Build spec content as a list of lines to avoid f-string/dedent pitfalls
    spec_lines = [
        "# -*- mode: python ; coding: utf-8 -*-",
        "",
        "import os",
        "import PyQt5",
        "from PyInstaller.utils.hooks import collect_submodules, collect_data_files",
        "",
        "block_cipher = None",
        "",
        "# Location of PyQt5 plugins (platforms, imageformats, etc.)",
        "pyqt_plugin_dir = os.path.join(PyQt5.__path__[0], 'Qt', 'plugins')",
        "",
        "datas = [",
        "    ('README.md', '.'),",
        "    ('requirements.txt', '.'),",
        "]",
        "",
        "# Include assets and PyQt5 plugins",
        "# `Tree` helper for bundling folders (implemented here to avoid PyInstaller API changes)",
        "def Tree(source, prefix=None):",
        "    result = []",
        "    for root, dirs, files in __import__('os').walk(source):",
        "        for fn in files:",
        "            src = __import__('os').path.join(root, fn)",
        "            rel = __import__('os').path.relpath(root, source)",
        "            if rel == '.':",
        "                dest_dir = prefix if prefix else ''",
        "            else:",
        "                dest_dir = __import__('os').path.join(prefix if prefix else '', rel)",
        "            result.append((src, dest_dir))",
        "    return result",
        "",
        "datas = datas + Tree('assets', prefix='assets') + Tree(pyqt_plugin_dir, prefix=__import__('os').path.join('PyQt5', 'Qt', 'plugins'))",
        "",
        "# Optionally include VLC native files (copy entire folder under 'vlc/')",
    ]

    # Insert vlc_tree lines (may be just a newline)
    spec_lines.extend(vlc_tree.splitlines())
    spec_lines.append("")

    spec_lines.extend([
        "# Hidden imports to help PyInstaller collect dynamic backends",
        "hiddenimports = [",
        "    'PyQt5.QtCore',",
        "    'PyQt5.QtGui',",
        "    'PyQt5.QtWidgets',",
        "    'matplotlib.backends.backend_qt5agg',",
        "    'matplotlib.backends.backend_agg',",
        "    'numpy',",
        "]",
        "",
        "a = Analysis(",
        "    ['launch_enhanced.py'],",
        "    pathex=[],",
        "    binaries=[],",
        "    datas=datas,",
        "    hiddenimports=hiddenimports,",
        "    hookspath=[],",
        "    hooksconfig={},",
        "    runtime_hooks=[],",
        "    excludes=['tkinter'],",
        "    win_no_prefer_redirects=False,",
        "    win_private_assemblies=False,",
        "    cipher=block_cipher,",
        "    noarchive=False,",
        ")",
        "",
        "pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)",
        "",
        "exe = EXE(",
        "    pyz,",
        "    a.scripts,",
        "    [],",
        "    exclude_binaries=True,",
        "    name='WinLink',",
        "    debug=False,",
        "    bootloader_ignore_signals=False,",
        "    strip=False,",
        "    upx=False,",
        "    console=False,",
        "    disable_windowed_traceback=False,",
        "    argv_emulation=False,",
        "    target_arch=None,",
        "    codesign_identity=None,",
        "    entitlements_file=None,",
        "    icon='assets/WinLink_logo.ico',",
        ")",
        "",
        "coll = COLLECT(",
        "    exe,",
        "    a.binaries,",
        "    a.zipfiles,",
        "    a.datas,",
        "    strip=False,",
        "    upx=False,",
        "    upx_exclude=[],",
        "    name='WinLink',",
        ")",
    ])

    spec_content = "\n".join(spec_lines) + "\n"

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


def find_inno_compiler():
    """Try to locate Inno Setup Compiler (ISCC.exe) on the system."""
    # Check PATH first
    iscc = shutil.which('iscc')
    if iscc:
        return iscc

    # Common install locations
    candidates = [
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe",
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return None


def create_inno_installer(prod_dir='WinLink_Production', output_dir='dist'):
    """Create a Windows installer using Inno Setup (ISCC).

    Returns path to generated installer exe on success, or None on failure.
    """
    print('\nAttempting to create Inno Setup installer...')

    if not os.path.exists(prod_dir):
        print(f"✗ Production directory not found: {prod_dir}")
        return None


    iscc = find_inno_compiler()
    if not iscc:
        print("✗ Inno Setup Compiler (ISCC.exe) not found. Install Inno Setup to create an installer:")
        print("  https://jrsoftware.org/isinfo.php")
        return None

    # Prepare working paths
    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M')
    iss_name = f'WinLink_{timestamp}.iss'
    iss_path = os.path.abspath(iss_name)
    # Installer filename (no timestamp) as requested
    output_base = 'WinLink_Installer'

    # Build the ISS script
    prod_abs = os.path.abspath(prod_dir)
    # Prefer the icon packaged inside the production WinLink folder
    prod_icon = os.path.join(prod_abs, 'WinLink', 'assets', 'WinLink_logo.ico')
    # Fallback to project-level assets folder if production copy missing
    project_icon = os.path.abspath('assets/WinLink_logo.ico') if os.path.exists('assets/WinLink_logo.ico') else ''
    icon_path = prod_icon if os.path.exists(prod_icon) else (project_icon if project_icon else '')

    # Put Tasks after [Setup] and explicitly install the WinLink subfolder into {app}\WinLink
    iss_lines = [
        '[Setup]',
        f'AppName=WinLink',
        f'AppVersion=2.0',
        'DefaultDirName={pf}\WinLink',
        'DefaultGroupName=WinLink',
        f'OutputBaseFilename={output_base}',
        'Compression=lzma',
        'SolidCompression=yes',
        'WizardStyle=modern',
        'DisableDirPage=no',
        'DirExistsWarning=yes',
        'PrivilegesRequired=admin',
        '',
        '[Tasks]',
        'Name: "desktopicon"; Description: "Create a desktop icon"; GroupDescription: "Additional tasks:"',
        '',
        '[Files]',
        # Copy only the WinLink folder contents into {app}\WinLink to avoid nested production folders
        f'Source: "{os.path.join(prod_abs, "WinLink", "*")}"; DestDir: "{{app}}\\WinLink"; Flags: recursesubdirs createallsubdirs',
    ]

    # If we have an icon file available inside the production package (or project),
    # add it to the [Files] section so the installer will install it into {app}.
    if icon_path:
        # Install the icon into the application folder (so shortcuts can reference {app}\WinLink_logo.ico)
        iss_lines.append(f'Source: "{icon_path}"; DestDir: "{{app}}"; Flags: ignoreversion')

    iss_lines.append('')
    iss_lines.append('[Icons]')

    # Add Start Menu shortcut and optional desktop icon (controlled by task).
    # Use the installed icon path ({app}\WinLink_logo.ico) instead of an absolute build-machine path.
    if icon_path:
        iss_lines.append('Name: "{group}\\WinLink"; Filename: "{app}\\WinLink\\WinLink.exe"; IconFilename: "{app}\\WinLink_logo.ico"; Tasks: desktopicon')
        iss_lines.append('Name: "{userdesktop}\\WinLink"; Filename: "{app}\\WinLink\\WinLink.exe"; IconFilename: "{app}\\WinLink_logo.ico"; Tasks: desktopicon')
    else:
        iss_lines.append('Name: "{group}\\WinLink"; Filename: "{app}\\WinLink\\WinLink.exe"; Tasks: desktopicon')
        iss_lines.append('Name: "{userdesktop}\\WinLink"; Filename: "{app}\\WinLink\\WinLink.exe"; Tasks: desktopicon')

    iss_lines.extend([
        '',
        '[Run]',
        # Run the EXE directly (more reliable than batch file)
        'Filename: "{app}\\WinLink\\WinLink.exe"; Description: "Launch WinLink"; Flags: nowait postinstall skipifsilent',
    ])

    # Write ISS file
    with open(iss_path, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(iss_lines))

    print(f"Using ISCC at: {iscc}")
    print(f"Created ISS script: {iss_path}")

    # Run ISCC to build installer
    try:
        subprocess.check_call([iscc, iss_path])
    except subprocess.CalledProcessError as e:
        print(f"✗ Inno Setup compilation failed: {e}")
        return None
    except Exception as e:
        print(f"✗ Failed to run ISCC: {e}")
        return None

    # Inno outputs installer exe in the same folder with name OutputBaseFilename.exe
    installer_name = f'{output_base}.exe'

    # Common ISCC output locations: current working dir and 'Output' subfolder.
    possible_paths = [
        os.path.join(os.getcwd(), installer_name),
        os.path.join(os.getcwd(), 'Output', installer_name),
    ]

    installer_path = None
    for p in possible_paths:
        if os.path.exists(p):
            installer_path = p
            break

    # If not found yet, search recursively under cwd (covers uncommon configs)
    if not installer_path:
        for root, dirs, files in os.walk(os.getcwd()):
            if installer_name in files:
                installer_path = os.path.join(root, installer_name)
                break

    if installer_path and os.path.exists(installer_path):
        os.makedirs(output_dir, exist_ok=True)
        final_path = os.path.join(output_dir, installer_name)
        # If an installer already exists at destination, replace it
        try:
            if os.path.exists(final_path):
                os.remove(final_path)
            shutil.move(installer_path, final_path)
            print(f"✓ Installer created: {final_path}")
            return final_path
        except Exception:
            print(f"✓ Installer created: {installer_path}")
            return installer_path

    print(f"✗ Installer not found after build: expected {installer_name} under cwd or Output/ folder")
    return None


def find_nsis_compiler():
    """Try to locate NSIS compiler (makensis.exe) on the system."""
    nsis = shutil.which('makensis')
    if nsis:
        return nsis

    candidates = [
        r"C:\Program Files (x86)\NSIS\makensis.exe",
        r"C:\Program Files\NSIS\makensis.exe",
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return None


def create_nsis_installer(prod_dir='WinLink_Production', output_dir='dist'):
    """Create a Windows installer using NSIS (makensis).

    Returns path to generated installer exe on success, or None on failure.
    """
    print('\nAttempting to create NSIS installer...')

    if not os.path.exists(prod_dir):
        print(f"✗ Production directory not found: {prod_dir}")
        return None

    makensis = find_nsis_compiler()
    if not makensis:
        print("✗ NSIS compiler (makensis.exe) not found. Install NSIS to create an installer:")
        print("  https://nsis.sourceforge.io/")
        return None

    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M')
    nsi_name = f'WinLink_{timestamp}.nsi'
    # Fixed NSIS installer filename (no timestamp)
    out_name = 'WinLink_NSIS_Installer.exe'
    nsi_path = os.path.abspath(nsi_name)

    prod_abs = os.path.abspath(prod_dir)
    winlink_dir = os.path.join(prod_abs, 'WinLink')
    if not os.path.exists(winlink_dir):
        print(f"✗ Expected WinLink directory not found inside {prod_dir}")
        return None

    # Build a simple NSIS script with a components page so user can choose shortcuts
    nsi_lines = [
        f'OutFile "{out_name}"',
        'InstallDir "$PROGRAMFILES\\WinLink"',
        'Page components',
        'Page directory',
        'Page instfiles',
        'Section "Main Files" SEC01',
        f'  SetOutPath "$INSTDIR"',
        f'  File /r "{winlink_dir}\\*.*"',
        'SectionEnd',
        'Section "Create Shortcuts" SEC02',
        '  ; This section will be optional (user can uncheck it)\n',
        f'  CreateShortCut "$SMPROGRAMS\\WinLink.lnk" "$INSTDIR\\WinLink\\WinLink.exe"',
        f'  CreateShortCut "$DESKTOP\\WinLink.lnk" "$INSTDIR\\WinLink\\WinLink.exe"',
        'SectionEnd',
    ]

    with open(nsi_path, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(nsi_lines))

    print(f"Using makensis at: {makensis}")
    print(f"Created NSIS script: {nsi_path}")

    try:
        subprocess.check_call([makensis, nsi_path])
    except subprocess.CalledProcessError as e:
        print(f"✗ NSIS compilation failed: {e}")
        return None
    except Exception as e:
        print(f"✗ Failed to run makensis: {e}")
        return None

    # Move resulting installer to output_dir
    installer_path = os.path.join(os.getcwd(), out_name)
    if os.path.exists(installer_path):
        os.makedirs(output_dir, exist_ok=True)
        final_path = os.path.join(output_dir, out_name)
        try:
            if os.path.exists(final_path):
                os.remove(final_path)
            shutil.move(installer_path, final_path)
            print(f"✓ NSIS installer created: {final_path}")
            return final_path
        except Exception:
            print(f"✓ NSIS installer created: {installer_path}")
            return installer_path
    else:
        print(f"✗ NSIS installer not found after build: expected {installer_path}")
        return None

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
    print()
    # Step 6: Attempt to create native installer (Inno Setup -> NSIS fallback)
    installer_path = create_inno_installer(prod_dir='WinLink_Production', output_dir='dist')
    if not installer_path:
        print("Inno Setup not available or failed — trying NSIS (makensis)...")
        installer_path = create_nsis_installer(prod_dir='WinLink_Production', output_dir='dist')

    if installer_path:
        print(f"\n✓ Native installer created: {installer_path}")
        print("You can distribute this single EXE to users; running it will show an installation wizard.")
    else:
        print("\n⚠️ Native installer was not created. The production folder is available in WinLink_Production/.")
        print("To create an installer, install Inno Setup (https://jrsoftware.org/isinfo.php) or NSIS (https://nsis.sourceforge.io/) and re-run this script.")
    
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
