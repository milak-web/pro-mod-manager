# PRO Mod Manager

Professional Windows mod profile manager for switching game mod setups safely and fast.

![PRO Mod Manager Icon](assets/app-icon.png)

## Overview

PRO Mod Manager helps you:

- Create and switch mod profiles per game.
- Activate/deactivate mods with tracked file operations.
- Keep local profile state in JSON for reliable rollback.
- Use either a native portable EXE or a full installer release.

## Project Status

This repository is now **source-first**.

- Source code is included and versioned.
- Build scripts and installer script are included.
- Binary files are distributed through **GitHub Releases**.

## Repository Structure

```text
src/                     # Main Python application source
scripts/                 # Build helpers (native EXE)
installer/               # Inno Setup script for installer
assets/                  # Project icon and visual assets
docs/                    # GitHub Pages website
```

## Run From Source

1. Install Python 3.11+.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run app:

```bash
python src/pro_mod_manager.py
```

## Build Native EXE

```bash
python scripts/build_exe.py
```

## Build Installer

Use Inno Setup Compiler with:

```text
installer/mod_manager_setup_clean.iss
```

## Downloads

- Latest Release page:
  - [https://github.com/milak-web/pro-mod-manager/releases/latest](https://github.com/milak-web/pro-mod-manager/releases/latest)

Release assets include:

- `PRO_Mod_Manager_Native.exe`
- `PRO_Mod_Manager_Setup.exe`

## Website

- Live site: [https://milak-web.github.io/pro-mod-manager/](https://milak-web.github.io/pro-mod-manager/)

## License

Personal project by MK2. Add a license file if you want public reuse permissions.
