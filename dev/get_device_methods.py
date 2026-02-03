#!/usr/bin/env python3
"""Get device methods and writable properties from Dreame cloud."""

import argparse
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import importlib.util

# Load cloud_base module
spec = importlib.util.spec_from_file_location(
    "cloud_base",
    project_root / "custom_components" / "dreame_mower" / "dreame" / "cloud" / "cloud_base.py"
)
cloud_base = importlib.util.module_from_spec(spec)
sys.modules["cloud_base"] = cloud_base
spec.loader.exec_module(cloud_base)


def main():
    parser = argparse.ArgumentParser(description="Get device methods and properties")
    parser.add_argument("--username", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--country", default="cn")
    parser.add_argument("--account-type", default="dreame", choices=["dreame", "mova"])
    parser.add_argument("--device-id", required=True)
    args = parser.parse_args()

    print(f"\n[*] Connecting to Dreame cloud ({args.account_type}, {args.country})...")
    print(f"    Device ID: {args.device_id}\n")

    # Create cloud client
    cloud = cloud_base.DreameMowerCloudBase(
        username=args.username,
        password=args.password,
        country=args.country,
        account_type=args.account_type,
    )

    # Connect
    print("[*] Attempting to connect...")
    if not cloud.connect():
        print("\n[!] Failed to connect")
        return 1

    print("[+] Connected!\n")

    # Get devices
    print("[*] Getting device list...")
    devices = cloud.get_devices()

    if not devices or "page" not in devices:
        print("[!] Failed to get devices")
        return 1

    # Find target device
    target_device = None
    records = devices["page"].get("records", [])
    for device in records:
        if device.get("did") == args.device_id:
            target_device = device
            break

    if not target_device:
        print(f"[!] Device {args.device_id} not found")
        return 1

    print(f"[+] Found device: {target_device.get('customName')}")
    print(f"    Model: {target_device.get('model')}")
    print()

    # Try to get device props (properties)
    print("="*60)
    print("GETTING DEVICE PROPERTIES")
    print("="*60)

    # The API strings array contains endpoint paths
    # Try different endpoints that might return property/method lists
    api = cloud._api_strings

    # Method 1: Try deviceprops endpoint (like get_device_info.py does)
    print("\n[*] Method 1: Trying deviceprops endpoint...")

    # Looking at the code, api_strings[20] is used for device props
    if len(api) > 20:
        props_data = api[20].replace("{did}", args.device_id)
        props_url = f"{cloud.get_api_url()}/home/deviceprops"
        print(f"    Data length: {len(props_data)}")
        print(f"    First 100 chars: {props_data[:100]}")

        try:
            response = cloud._session.post(
                props_url,
                data=props_data,
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "User-Agent": api[11],
                },
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                print(f"    Response code: {data.get('code')}")
                print(f"    Response keys: {list(data.keys())}")
                print(f"    Full response: {json.dumps(data, indent=2, ensure_ascii=False)[:500]}...")

                if data.get("code") == 0:
                    if "data" in data:
                        print(f"    Data type: {type(data['data'])}")
                        if isinstance(data['data'], dict):
                            print(f"    Data keys: {list(data['data'].keys())}")

                    if "result" in data.get("data", {}):
                        result = data["data"]["result"]
                        print(f"[+] Got {len(result)} properties:\n")

                    # Group by siid and find writable ones
                    by_siid = {}
                    writable_props = []

                    for prop in result:
                        siid = prop.get("siid")
                        if siid not in by_siid:
                            by_siid[siid] = []
                        by_siid[siid].append(prop)

                        # Check if writable
                        access = prop.get("definition", {}).get("access", "")
                        if "write" in access.lower():
                            writable_props.append(prop)

                    # Print all properties grouped by siid
                    for siid in sorted(by_siid.keys()):
                        print(f"Service {siid}:")
                        for prop in by_siid[siid]:
                            piid = prop.get("piid")
                            name = prop.get("name", "Unknown")
                            value = prop.get("value", "N/A")
                            access = prop.get("definition", {}).get("access", "")
                            writable = "🔴 WRITABLE" if "write" in access.lower() else ""
                            print(f"  [{siid}:{piid}] {name} = {value} ({access}) {writable}")
                        print()

                    # Show writable properties
                    if writable_props:
                        print("="*60)
                        print("WRITABLE PROPERTIES")
                        print("="*60 + "\n")

                        for prop in writable_props:
                            siid = prop.get("siid")
                            piid = prop.get("piid")
                            name = prop.get("name", "Unknown")
                            value = prop.get("value", "N/A")
                            format_str = prop.get("definition", {}).get("format", "str")

                            print(f"[{siid}:{piid}] {name}")
                            print(f"  Current value: {value}")
                            print(f"  Format: {format_str}")
                            print(f"  To set: coordinator.device.set_property({siid}, {piid}, <value>)")
                            print()
                    else:
                        print("[!] No writable properties found\n")

        except Exception as ex:
            print(f"[!] Failed: {ex}")

    # Method 2: Try methodlist endpoint
    print("="*60)
    print("GETTING DEVICE METHODS/ACTIONS")
    print("="*60)

    method_attempts = [
        "/home/methodlist",
        "/home/devicefunctions",
        "/homeroom/functions",
        "/rpc/methodlist",
    ]

    for endpoint in method_attempts:
        print(f"\n[*] Trying: {endpoint}")

        try:
            # Try with the device props data format
            methods_data = api[20].replace("{did}", args.device_id) if len(api) > 20 else f'{{"did":"{args.device_id}"}}'
            methods_url = f"{cloud.get_api_url()}{endpoint}"

            response = cloud._session.post(
                methods_url,
                data=methods_data,
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "User-Agent": api[11],
                },
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("code") == 0:
                    # Check different response structures
                    result = None
                    if "result" in data.get("data", {}):
                        result = data["data"]["result"]
                    elif "result" in data:
                        result = data["result"]
                    elif "data" in data and isinstance(data["data"], list):
                        result = data["data"]

                    if result:
                        print(f"[+] SUCCESS! Got {len(result)} methods:\n")

                        # Group by siid
                        by_siid = {}
                        for method in result:
                            siid = method.get("siid")
                            if siid not in by_siid:
                                by_siid[siid] = []
                            by_siid[siid].append(method)

                        # Print grouped
                        for siid in sorted(by_siid.keys()):
                            print(f"Service {siid}:")
                            for method in by_siid[siid]:
                                aiid = method.get("aiid")
                                name = method.get("name", "Unknown")
                                description = method.get("description", "")
                                print(f"  [{siid}:{aiid}] {name}")
                                if description:
                                    print(f"      → {description}")
                            print()

                        # Look for clean/dry methods
                        print("\n" + "="*60)
                        print("CLEAN/DRY RELATED METHODS")
                        print("="*60 + "\n")

                        keywords = ["clean", "wash", "self", "dry", "roll", "mop", "洗", "烘干", "自清洁", "hot", "deep"]
                        for method in result:
                            name = method.get("name", "").lower()
                            siid = method.get("siid")
                            aiid = method.get("aiid")

                            if any(k in name for k in keywords):
                                print(f"✓ [{siid}:{aiid}] {method.get('name')}")
                                print(f"  ActionIdentifier(siid={siid}, aiid={aiid}, name=\"{method.get('name')}\")")
                                print()

                        return 0

        except Exception as ex:
            print(f"[!] Failed: {ex}")

    print("\n[!] Could not find method list via API")
    print("[*] Try using mitmproxy to capture app traffic (see PACKET_CAPTURE_GUIDE.md)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
