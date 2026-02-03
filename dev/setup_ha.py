#!/usr/bin/env python3
"""Setup script to deploy Dreame Mower integration to Home Assistant."""

import os
import shutil
from pathlib import Path
import sys

def find_ha_config():
    """Find Home Assistant configuration directory."""
    print("[*] Looking for Home Assistant configuration directory...")

    # Common paths for different OS
    possible_paths = []

    if sys.platform == "win32":
        # Windows
        possible_paths = [
            Path(os.environ.get("APPDATA", "")) / "Home Assistant" / ".homeassistant",
            Path("C:/HomeAssistant/.homeassistant"),
            Path("D:/HomeAssistant/.homeassistant"),
        ]
    elif sys.platform == "darwin":
        # macOS
        possible_paths = [
            Path.home() / ".homeassistant",
        ]
    else:
        # Linux
        possible_paths = [
            Path.home() / ".homeassistant",
            Path("/home/homeassistant/.homeassistant"),
        ]

    # Check if paths exist
    for path in possible_paths:
        if path.exists() and (path / "configuration.yaml").exists():
            print(f"[+] Found HA config: {path}")
            return path

    print("[!] Could not find HA config directory automatically")
    print()
    print("Common locations:")
    print("  Windows: %APPDATA%\\Home Assistant\\.homeassistant")
    print("  macOS: ~/.homeassistant")
    print("  Linux: ~/.homeassistant")
    print()
    return None


def check_integration_exists(ha_config):
    """Check if dreame_mower integration already exists."""
    integration_path = ha_config / "custom_components" / "dreame_mower"

    if integration_path.exists():
        print(f"[+] Integration already exists at: {integration_path}")
        print()
        print("Current files:")
        for file in sorted(integration_path.rglob("*")):
            if file.is_file():
                print(f"  - {file.relative_to(integration_path)}")
        return True
    else:
        print(f"[!] Integration not found")
        return False


def copy_integration(project_root, ha_config):
    """Copy integration files to HA config."""
    print()
    print("[*] Copying integration files...")

    # Source and destination
    src_dir = project_root / "custom_components" / "dreame_mower"
    dst_dir = ha_config / "custom_components" / "dreame_mower"

    # Create destination if it doesn't exist
    dst_dir.parent.mkdir(parents=True, exist_ok=True)

    # Remove old version if exists
    if dst_dir.exists():
        print(f"[*] Removing old version...")
        shutil.rmtree(dst_dir)

    # Copy directory
    print(f"[*] Copying {src_dir} -> {dst_dir}")
    shutil.copytree(src_dir, dst_dir)

    file_count = len(list(dst_dir.rglob('*')))
    print(f"[+] Successfully copied {file_count} files")


def main():
    print("="*60)
    print("Dreame Mower Integration - Setup Assistant")
    print("="*60)
    print()

    # Get project root
    project_root = Path(__file__).parent.parent

    # Find HA config
    ha_config = find_ha_config()

    if not ha_config:
        print()
        ha_config_input = input("\nPlease enter your HA config directory path: ").strip()
        ha_config = Path(ha_config_input)
        if not ha_config.exists():
            print(f"[!] Path does not exist: {ha_config}")
            return 1

    print()

    # Check if integration already exists
    exists = check_integration_exists(ha_config)

    # Ask what to do
    if exists:
        print()
        choice = input("Integration already exists. Overwrite? [y/N]: ").strip().lower()
        if choice != 'y':
            print("[*] Skipping file copy")
        else:
            copy_integration(project_root, ha_config)
    else:
        copy_integration(project_root, ha_config)

    print()
    print("="*60)
    print("Setup complete!")
    print("="*60)
    print()
    print("Next steps:")
    print("  1. Restart Home Assistant")
    print("  2. Add integration via UI:")
    print("     - Settings → Devices & Services → Add Integration")
    print("     - Search 'Dreame Mower'")
    print("     - Enter your credentials")
    print("     - Select H20 Ultra device")
    print()

    # Offer to restart HA
    if sys.platform == "win32":
        print("To restart HA on Windows:")
        print("  - Use Home Assistant Supervisor")
        print("  - Or: Settings → System → Restart")
    elif sys.platform == "darwin":
        print("To restart HA on macOS:")
        print("  - Click Restart in the menu")
    else:
        print("To restart HA on Linux:")
        print("  - ha core restart")
        print("  - Or: systemctl restart home-assistant")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
