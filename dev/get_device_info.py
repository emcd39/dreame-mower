#!/usr/bin/env python3
"""Simple tool to get device info from Dreame cloud."""

import argparse
import base64
import hashlib
import json
import re
import zlib
from pathlib import Path

import requests


def load_api_strings():
    """Load API strings."""
    project_root = Path(__file__).parent.parent
    cloud_base_path = project_root / "custom_components" / "dreame_mower" / "dreame" / "cloud" / "cloud_base.py"

    with open(cloud_base_path, 'r') as f:
        content = f.read()

    match = re.search(r'DREAME_STRINGS.*?=.*?"([^"]+)"', content, re.DOTALL)
    if not match:
        raise ValueError("Could not find DREAME_STRINGS")

    encoded = match.group(1)
    return json.loads(zlib.decompress(base64.b64decode(encoded), zlib.MAX_WBITS | 32))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--username", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--country", default="cn")
    parser.add_argument("--device-id", required=True)
    args = parser.parse_args()

    api_strings = load_api_strings()

    print(f"\n[*] Connecting to Dreame cloud ({args.country})...")
    print(f"[+] Device ID: {args.device_id}\n")

    session = requests.Session()

    # Login
    login_data = (f"{api_strings[12]}{api_strings[14]}"
                 f"{args.username}{api_strings[15]}"
                 f"{hashlib.md5((args.password + api_strings[2]).encode()).hexdigest()}"
                 f"{api_strings[16]}")

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": api_strings[11],
    }

    url = f"https://{args.country}{api_strings[0]}:{api_strings[1]}/app/v1/login"
    resp = session.post(url, data=login_data, headers=headers, timeout=30)

    if resp.status_code != 200 or resp.json().get("code") != 0:
        print("[!] Login failed")
        return 1

    print("[+] Logged in\n")

    # Get device props
    print("="*60)
    print("GETTING DEVICE PROPERTIES")
    print("="*60)

    props_url = f"https://{args.country}{api_strings[0]}:{api_strings[1]}/home/deviceprops"
    props_data = api_strings[20].replace("{did}", args.device_id)

    resp = session.post(props_url, data=props_data, headers=headers, timeout=30)

    if resp.status_code == 200:
        data = resp.json()
        if data.get("code") == 0 and "result" in data:
            result = data["result"]
            print(f"\n[+] Got {len(result)} properties:\n")

            # Group by siid
            by_siid = {}
            for prop in result:
                siid = prop.get("siid")
                if siid not in by_siid:
                    by_siid[siid] = []
                by_siid[siid].append(prop)

            # Print grouped
            for siid in sorted(by_siid.keys()):
                print(f"Service {siid}:")
                for prop in by_siid[siid]:
                    piid = prop.get("piid")
                    name = prop.get("name", "Unknown")
                    value = prop.get("value", "N/A")
                    access = prop.get("definition", {}).get("access", "")
                    print(f"  [{siid}:{piid}] {name} = {value} ({access})")
                print()

    # Try to get methods
    print("="*60)
    print("TRYING TO GET METHODS")
    print("="*60)

    # Try different method list endpoints
    method_attempts = [
        f"https://{args.country}{api_strings[0]}:{api_strings[1]}/home/methodlist",
        f"https://{args.country}{api_strings[0]}:{api_strings[1]}/home/devicefunctions",
    ]

    for method_url in method_attempts:
        print(f"\n[*] Trying: {method_url}")

        if len(api_strings) > 21:
            methods_data = api_strings[21].replace("{did}", args.device_id)
        else:
            # Try generic data
            methods_data = api_strings[20].replace("{did}", args.device_id)

        try:
            resp = session.post(method_url, data=methods_data, headers=headers, timeout=30)

            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == 0 and "result" in data:
                    result = data["result"]
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

                    keywords = ["clean", "wash", "self", "dry", "roll", "mop", "洗", "烘干", "自清洁"]
                    for method in result:
                        name = method.get("name", "").lower()
                        siid = method.get("siid")
                        aiid = method.get("aiid")

                        if any(k in name for k in keywords):
                            print(f"✓ [{siid}:{aiid}] {method.get('name')}")
                            print(f"  Update const.py:")
                            print(f'  HOLD_ACTION_START_{name.upper()} = ActionIdentifier(siid={siid}, aiid={aiid}, name="{name}")')
                            print()

                    return 0
        except Exception as ex:
            print(f"[!] Failed: {ex}")

    print("\n[!] Could not find method list via API")
    print("[*] Try using mitmproxy to capture app traffic")
    print("[*] See PACKET_CAPTURE_GUIDE.md for instructions")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
