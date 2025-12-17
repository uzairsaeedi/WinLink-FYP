# WinLink Production Packaging Guide

This document describes the recommended, up-to-date process to produce a production-ready Windows distribution (standalone folder with `WinLink.exe`) using the repository's automated build helper `build_exe.py`.

**Scope**: Windows desktop production builds (PyInstaller-based). This guide assumes you're building on a Windows machine.

---

## Prerequisites

- Python 3.8 or newer installed and on PATH
- Up-to-date `pip`
- A working Visual C++ runtime on build machine (typical on dev machines)
- Administrator rights for firewall/script testing on target machines

Install runtime dependencies used by the project:

```powershell
python -m pip install -r requirements.txt
```

Notes:

- `requirements.txt` now includes `numpy`, `pywin32`, and `python-vlc` (used by the worker video player). If you will NOT bundle VLC, installing `python-vlc` is still recommended for local testing.

---

## Build (Recommended - automated)

1. From project root, install requirements (see above).

2. Optionally set VLC path (only required if you want the build script to bundle VLC native files):

```powershell
:: Set VLC_PATH to an installed VLC folder (32/64-bit as appropriate)
setx VLC_PATH "C:\Program Files\VideoLAN\VLC"
:: or for current session only
set VLC_PATH=C:\"Program Files"\VideoLAN\VLC
```

3. Run the automated packaging helper:

```powershell
python build_exe.py
```

What `build_exe.py` does (summary):

- Generates a PyInstaller `.spec` tailored for this project (includes `assets` and application folders)
- Adds PyQt5 plugin folders into the spec so Qt runs correctly in the bundle
- Adds common `hiddenimports` (matplotlib backends, numpy, vlc) to avoid common "missing module" runtime failures
- Optionally bundles VLC native files into the distribution when `VLC_PATH` is detected or `BUNDLE_VLC` is enabled inside the script
- Disables UPX by default to avoid runtime DLL-load issues on some Windows hosts
- Invokes PyInstaller and builds `WinLink_Production/` folder

Output:

- `WinLink.spec` (generated)
- `dist/` and `build/` from PyInstaller (temporary)
- `WinLink_Production/` containing the final application folder for distribution

---

## Forcing VLC bundling (if needed)

The packaging helper will attempt to locate VLC on the build machine and include its native DLLs under `vlc/` in the final package. To ensure VLC is bundled:

- Install VLC (VideoLAN) on the build machine
- Set `VLC_PATH` environment variable to the VLC installation directory (example above)
- Re-run `python build_exe.py`

If you prefer editing the script, `build_exe.py` contains a `BUNDLE_VLC` toggle near the top — set it to `True` to attempt bundling.

Notes:

- Bundling VLC increases package size substantially (do this only when necessary)
- If you don't bundle VLC, end users must have VLC installed for the `python-vlc` playback path to work, or the app will fall back to an error dialog.

---

## Manual / Advanced (PyInstaller flags)

If you need manual control, you can run PyInstaller directly using the generated `.spec`:

```powershell
pyinstaller --clean WinLink.spec
```

Recommended PyInstaller options when customizing:

- `upx=False` — recommended to avoid runtime loading issues
- Include `datas` entries for the `assets/` folder and other non-Python files
- Add `hiddenimports` for any modules reported missing at runtime
- Ensure `binaries` includes any native DLLs you must ship

---

## Test Checklist (mandatory before distribution)

Test on at least one clean Windows machine (no Python installed):

- [ ] Copy `WinLink_Production/` to test machine
- [ ] Run `Start_WinLink.bat` and verify `WinLink.exe` launches
- [ ] Run Master and Worker roles and verify discovery and task execution
- [ ] Test video playback on a Worker (if relevant) — if VLC was bundled, verify it loads from the `vlc/` folder
- [ ] Run `setup_firewall.bat` on Worker and ensure network connectivity
- [ ] Inspect `WinLink/logs/` for errors and verify rotation
- [ ] Confirm application closes cleanly and no lingering processes remain

If you encounter issues, collect the build log (PyInstaller stdout/stderr) and the runtime logs from `WinLink/logs/`.

---

## Common Troubleshooting Notes

- "Failed to execute script" — check generated `.spec` for missing `hiddenimports` and add them.
- Missing DLL — add the DLL to `binaries` or `datas` in the `.spec`.
- Qt plugin errors (platform plugin not found) — ensure PyInstaller includes the Qt `platforms` plugin folder (the automated script does this).
- Large binary size — disable VLC bundling, trim unused libs, consider `--onefile` (note: slower startup).
- Intermittent socket errors on Windows (e.g. WinError 10038) — these are typically runtime socket lifecycle races. Reproduce with logs and include both build-time and runtime logs when filing an issue; build-time changes are unlikely to fix these without code instrumentation.

---

## Signing and Installer (recommended for distribution)

1. Code-sign the main executable to avoid "Unknown Publisher" warnings.

```powershell
signtool sign /f certificate.pfx /p password /t http://timestamp.digicert.com "WinLink_Production\WinLink\WinLink.exe"
```

2. Create an installer using Inno Setup or NSIS. Example Inno Setup snippet (adapt `Source`):

```iss
[Setup]
AppName=WinLink
AppVersion=2.0
DefaultDirName={pf}\WinLink
OutputDir=Output
OutputBaseFilename=WinLink_Setup

[Files]
Source: "WinLink_Production\*"; DestDir: "{app}"; Flags: recursesubdirs

[Icons]
Name: "{commondesktop}\WinLink"; Filename: "{app}\Start_WinLink.bat"
```

Signing tip: sign before creating the installer so both the exe and installer can be signed.

---

## Release Checklist

- [ ] Build artifacts present in `WinLink_Production/`
- [ ] Tested on clean Windows machine(s)
- [ ] `Start_WinLink.bat` and `setup_firewall.bat` included and verified
- [ ] Optional VLC bundling verified or clear instructions provided to end users
- [ ] Executable code-signed (recommended)
- [ ] Installer created and optionally signed

---

## Quick Commands (copy-paste)

```powershell
python -m pip install -r requirements.txt
:: Optionally set VLC path if you want it bundled
set VLC_PATH=C:\"Program Files"\VideoLAN\VLC
python build_exe.py

# After build: compress or make installer
Compress-Archive -Path WinLink_Production -DestinationPath WinLink_v2.0.zip
```

---

If you'd like, I can also:

- add a short `PACKAGING_CHECKLIST.md` that your CI or release engineer can follow,
- or add a small `build_test.ps1` that runs smoke tests against the produced `WinLink_Production` folder.

End of packaging guide.

- [ ] License.txt (if applicable)

### End User Instructions

1. Extract WinLink_Production.zip
2. Run setup_firewall.bat as Administrator (worker PCs only)
3. Launch Start_WinLink.bat
4. Choose role: Master or Worker
5. Configure network settings if needed

---

## Conclusion

Your WinLink application is now production-ready! The automated build script handles most complexity, and the resulting package is easy to distribute and install.

**Final checklist:**

- ✓ Executable built successfully
- ✓ Production package created
- ✓ Essential .bat files included
- ✓ Development files excluded
- ✓ Tested on clean system
- ✓ Ready for distribution

For questions or issues, refer to the main README.md or contact support.
