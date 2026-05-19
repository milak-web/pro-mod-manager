from pathlib import Path
import shutil
import PyInstaller.__main__


ROOT = Path(__file__).resolve().parents[1]
SRC_FILE = ROOT / "src" / "pro_mod_manager.py"
ICON_FILE = ROOT / "assets" / "mod_manager_new.ico"
BUILD_DIR = ROOT / "build"
DIST_DIR = ROOT / "dist"


def main() -> None:
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)

    args = [
        str(SRC_FILE),
        "--name=PRO_Mod_Manager_Native",
        "--onefile",
        "--windowed",
        "--clean",
        "--noconfirm",
    ]

    if ICON_FILE.exists():
        args.append(f"--icon={ICON_FILE}")

    PyInstaller.__main__.run(args)
    print("SUCCESS: dist/PRO_Mod_Manager_Native.exe created.")


if __name__ == "__main__":
    main()
