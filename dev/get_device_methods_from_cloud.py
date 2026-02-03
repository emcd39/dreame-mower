#!/usr/bin/env python3
"""Get device methods from Dreame cloud API."""

import sys
import importlib.util
import json
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

    # Load cloud_device
    spec_device = importlib.util.spec_from_file_location(
        "dreame_mower.dreame.cloud.cloud_device",
        project_root / "custom_components" / "dreame_mower" / "dreame" / "cloud" / "cloud_device.py"
    )
    cloud_device = importlib.util.module_from_spec(spec_device)
    sys.modules["dreame_mower.dreame.cloud.cloud_device"] = cloud_device
    spec_device.loader.exec_module(cloud_device)

    return cloud_device


def get_device_methods(username, password, country, device_id):
    """Get device methods from cloud API."""
    cloud_base = load_cloud_modules()

    print(f"[*] Connecting to Dreame cloud ({args.country})...")

    # Create auth
    auth = cloud_base.DreameMowerCloudBase(
        username=username,
        password=password,
        country=country,
        account_type="dreame",
    )

    auth.connect()

    if not auth.connected:
        print("[!] Failed to connect")
        return None

    print("[+] Connected")

    # Get devices
    devices = auth.get_devices()
    if not devices or "page" not in devices:
        print("[!] No devices found")
        return None

    # Find target device
    target_device = None
    for device in devices["page"].get("records", []):
        if device.get("did") == device_id:
            target_device = device
            break

    if not target_device:
        print(f"[!] Device {device_id} not found")
        return None

    print(f"\n[+] Found device: {target_device.get('customName')}")
    print(f"    Model: {target_device.get('model')}")
    print(f"    MAC: {target_device.get('mac')}")

    # Try to get device spec/methods
    # The cloud API may have a method to get device capabilities
    # Let's try different endpoints

    print("\n[*] Attempting to get device methods...")

    # Method 1: Try to get homeroom info (may include methods)
    try:
        import requests
        session = requests.Session()

        # Load API strings
        from custom_components.dreame_mower.dreame.cloud.cloud_base import DreameMowerCloudBase
        api_strings = DreameMowerCloudBase._get_api_strings()

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": api_strings[11],
        }

        # Try getting device props
        props_data = api_strings[20].replace("{did}", device_id)
        props_url = f"https://{country}{api_strings[0]}:{api_strings[1]}/home/deviceprops"

        resp = session.post(props_url, data=props_data, headers=headers, timeout=30)
        print(f"\n[*] Device Properties API:")
        print(f"    URL: {props_url}")
        print(f"    Status: {resp.status_code}")

        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == 0 and "result" in data:
                print(f"\n[+] Got device properties!")
                result = data["result"]

                if isinstance(result, list):
                    print(f"\n[*] Found {len(result)} properties:")
                    for i, prop in enumerate(result[:10]):  # Show first 10
                        siid = prop.get("siid")
                        piid = prop.get("piid")
                        name = prop.get("name", "Unknown")
                        value = prop.get("value")
                        print(f"    {i+1}. [{siid}:{piid}] {name} = {value}")

                    if len(result) > 10:
                        print(f"    ... and {len(result) - 10} more")

        # Try getting device methods/functions
        # This might be in a different endpoint
        print(f"\n[*] Looking for methods/actions...")

        # Check if there's a methodlist API string
        if len(api_strings) > 21:
            methods_data = api_strings[21].replace("{did}", device_id)
            methods_url = f"https://{country}{api_strings[0]}:{api_strings[1]}/home/methodlist"

            resp = session.post(methods_url, data=methods_data, headers=headers, timeout=30)
            print(f"\n[*] Device Methods API:")
            print(f"    URL: {methods_url}")
            print(f"    Status: {resp.status_code}")

            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == 0 and "result" in data:
                    print(f"\n[+] Got device methods!")
                    result = data["result"]

                    if isinstance(result, list):
                        print(f"\n[*] Found {len(result)} methods:")
                        for i, method in enumerate(result):
                            siid = method.get("siid")
                            aiid = method.get("aiid")
                            name = method.get("name", "Unknown")
                            description = method.get("description", "")
                            print(f"    {i+1}. [{siid}:{aiid}] {name}")
                            if description:
                                print(f"       Description: {description}")

                        # Look for self-clean related methods
                        print(f"\n[*] Self-clean related methods:")
                        for method in result:
                            name = method.get("name", "").lower()
                            siid = method.get("siid")
                            aiid = method.get("aiid")
                            if any(keyword in name for keyword in ["clean", "wash", "self", "dry", "roll", "mop"]):
                                print(f"    - [{siid}:{aiid}] {method.get('name')}")

    except Exception as ex:
        print(f"[!] Error: {ex}")
        import traceback
        traceback.print_exc()

    return True


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--username", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--country", default="cn")
    parser.add_argument("--device-id", required=True)
    args = parser.parse_args()

    result = get_device_methods(args.username, args.password, args.country, args.device_id)

    if result:
        print("\n[+] Done!")
    else:
        print("\n[!] Failed")
