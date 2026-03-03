#!/usr/bin/env python3
"""Build a downloadable DocsWriter zip that includes a local venv + dependencies."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parent
BUILD_DIR = ROOT / "build"
DIST_DIR = ROOT / "dist"
BUNDLE_NAME = "DocsWriterPortable"

RUNTIME_FILES = [
    "app.py",
    "docs_writer.py",
    "README.md",
    "LICENSE",
]

DEPENDENCIES = ["pyautogui", "pyperclip", "openai"]


def run(cmd: list[str], cwd: Path | None = None) -> None:
    subprocess.run(cmd, cwd=cwd, check=True)


def launcher_shell_text() -> str:
    return """#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname \"${BASH_SOURCE[0]}\")" && pwd)"
"$SCRIPT_DIR/.venv/bin/python" "$SCRIPT_DIR/app.py"
"""


def launcher_bat_text() -> str:
    return """@echo off
set SCRIPT_DIR=%~dp0
"%SCRIPT_DIR%\.venv\Scripts\python.exe" "%SCRIPT_DIR%\app.py"
"""


def build_portable_zip(skip_pip: bool) -> Path:
    bundle_dir = BUILD_DIR / BUNDLE_NAME
    if bundle_dir.exists():
        shutil.rmtree(bundle_dir)
    bundle_dir.mkdir(parents=True, exist_ok=True)

    for rel in RUNTIME_FILES:
        shutil.copy2(ROOT / rel, bundle_dir / rel)

    shutil.copy2(ROOT / ".env.example", bundle_dir / ".env")

    shell_launcher = bundle_dir / "run-docswriter.sh"
    shell_launcher.write_text(launcher_shell_text(), encoding="utf-8")
    shell_launcher.chmod(0o755)

    bat_launcher = bundle_dir / "run-docswriter.bat"
    bat_launcher.write_text(launcher_bat_text(), encoding="utf-8")

    venv_dir = bundle_dir / ".venv"
    run([sys.executable, "-m", "venv", str(venv_dir)])

    if sys.platform == "win32":
        python_bin = venv_dir / "Scripts" / "python.exe"
    else:
        python_bin = venv_dir / "bin" / "python"

    if not skip_pip:
        run([str(python_bin), "-m", "pip", "install", "--upgrade", "pip"])
        run([str(python_bin), "-m", "pip", "install", *DEPENDENCIES])

    DIST_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = DIST_DIR / f"{BUNDLE_NAME}.zip"
    if zip_path.exists():
        zip_path.unlink()

    with ZipFile(zip_path, "w", compression=ZIP_DEFLATED) as zf:
        for path in bundle_dir.rglob("*"):
            zf.write(path, path.relative_to(BUILD_DIR))

    return zip_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a downloadable DocsWriter zip bundle.")
    parser.add_argument(
        "--skip-pip",
        action="store_true",
        help="Create bundle and venv but skip dependency installation (useful in restricted CI).",
    )
    args = parser.parse_args()

    zip_path = build_portable_zip(skip_pip=args.skip_pip)
    print(f"Created: {zip_path}")


if __name__ == "__main__":
    main()
