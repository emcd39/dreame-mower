#!/usr/bin/env python3
"""Get available methods for Dreame hold device."""

import sys
import importlib.util
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def load_cloud_modules():
    """Load cloud modules bypassing __init__.py."""
    # Create synthetic module hierarchy
    sys.modules["dreame_mower"] = type(sys)("dreame_mower")
    sys.modules["dreame_mower.dreame"] = type(sys)("dreame_mower.dreame")
    sys.modules["dreame_mower.dreame.cloud"] = type(sys)("dreame_mower.dreame.cloud")

    # Load const first
    spec_const = importlib.util.spec_from_file_location(
        "dreame_mower.dreame.const",
        project_root / "custom_components" / "dreame_mower" / "dreame" / "const.py"
    )
    const_module = importlib.util.module_from_spec(spec_const)
    sys.modules["dreame_mower.dreame.const"] = const_module
    spec_const.loader.exec_module(const_module)

    # Load cloud_base
    spec_base = importlib.util.spec_from_file_location(
        "dreame_mower.dreame.cloud.cloud_base",
        project_root / "custom_components" / "dreame_mower" / "dreame" / "cloud" / "cloud_base.py"
    )
    cloud_base = importlib.util.module_from_spec(spec_base)
    sys.modules["dreame_mower.dreame.cloud.cloud_base"] = cloud_base
    spec_base.loader.exec_module(cloud_base)

    return cloud_base


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--username", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--country", default="cn")
    parser.add_argument("--device-id", required=True)
    args = parser.parse_args()

    # Load modules
    cloud_base = load_cloud_modules()

    print(f"\n[*] Connecting to Dreame cloud ({args.country})...")
    print(f"[+] Device ID: {args.device_id}\n")

    # Create auth instance
    auth = cloud_base.DreameMowerCloudBase(
        username=args.username,
        password=args.password,
        country=args.country,
        account_type="dreame",
    )

    # Connect
    import time
    auth.connect()

    if not auth.connected:
        print("[!] Failed to connect")
        return 1

    print("[+] Connected\n")

    # Get device info including methods
    # Try to get the device's spec/definition
    try:
        # Get device list to find our device
        devices = auth.get_devices()
        if devices and "page" in devices:
            records = devices["page"].get("records", [])
            for device in records:
                if device.get("did") == args.device_id:
                    print("="*60)
                    print("DEVICE INFO")
                    print("="*60)
                    print(f"Model: {device.get('model')}")
                    print(f"Name: {device.get('customName')}")
                    print(f"MAC: {device.get('mac')}")
                    print(f"SN: {device.get('sn')}")
                    print()

                    # Try to get method definitions
                    # This is a simplified approach - actual method discovery
                    # requires HTTP API calls to miot spec
                    print("="*60)
                    print("ATTEMPTING TO GET DEVICE SPECS")
                    print("="*60)

                    # The device's spec URL format for MIoT
                    model = device.get('model')
                    if model:
                        # MIoT spec URL format
                        spec_url = f"https://miot-spec.org/m/devicespec?model={model}"
                        print(f"\n[*] Check MIoT spec at:")
                        print(f"    {spec_url}")
                        print()
                        print("[*] Or use miot-spec-cli:")
                        print(f"    miot-spec dev get --model {model}")
                        print()
                        print("[*] This will show all available methods (actions)")
                        print("    Look for 'selfClean', 'wash', 'dry' etc.")
                        print()
                        print("[*] Format is: siid (Service ID) and aiid (Action ID)")
                        print("    Example: siid=6, aiid=1 means service 6, action 1")

                    break
    except Exception as ex:
        print(f"[!] Error: {ex}")
        import traceback
        traceback.print_exc()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
