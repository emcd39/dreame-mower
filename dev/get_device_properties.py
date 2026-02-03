#!/usr/bin/env python3
"""Get device properties and actions from MQTT API."""

import argparse
import base64
import hashlib
import json
import re
import zlib
from pathlib import Path

import requests


def load_api_strings():
    """Load API strings from original cloud_base.py file."""
    project_root = Path(__file__).parent.parent
    cloud_base_path = project_root / "custom_components" / "dreame_mower" / "dreame" / "cloud" / "cloud_base.py"

    with open(cloud_base_path, 'r') as f:
        content = f.read()

    # Extract DREAME_STRINGS using regex
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

    # Load API strings from original file
    api_strings = load_api_strings()

    print(f"\n[*] Connecting to Dreame cloud ({args.country})...")
    print(f"[+] Device ID: {args.device_id}\n")

    # Setup session
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

    # Get device properties
    props_url = f"https://{args.country}{api_strings[0]}:{api_strings[1]}/home/deviceprops"
    props_data = api_strings[20].replace("{did}", args.device_id)

    resp = session.post(props_url, data=props_data, headers=headers, timeout=30)

    if resp.status_code == 200:
        data = resp.json()
        if data.get("code") == 0 and "result" in data:
            result = data["result"]

            print("="*60)
            print("DEVICE PROPERTIES")
            print("="*60)

            if isinstance(result, list):
                for prop in result:
                    siid = prop.get("siid")
                    piid = prop.get("piid")
                    value = prop.get("value")
                    name = prop.get("name", "Unknown")

                    print(f"\n[{siid}:{piid}] {name}")
                    print(f"  Value: {value}")

                    # Show additional info if available
                    if "definition" in prop:
                        definition = prop["definition"]
                        if "format" in definition:
                            print(f"  Format: {definition['format']}")
                        if "access" in definition:
                            print(f"  Access: {definition['access']}")
                        if "unit" in definition:
                            print(f"  Unit: {definition['unit']}")

            print("\n" + "="*60)
            print("ACTIONS (Methods)")
            print("="*60)

            # Try to get actions/methods
            methods_url = f"https://{args.country}{api_strings[0]}:{api_strings[1]}/home/methodlist"
            methods_data = api_strings[21].replace("{did}", args.device_id) if 21 < len(api_strings) else None

            if methods_data:
                resp = session.post(methods_url, data=methods_data, headers=headers, timeout=30)
                if resp.status_code == 200:
                    methods = resp.json()
                    if methods.get("code") == 0 and "result" in methods:
                        for method in methods["result"]:
                            siid = method.get("siid")
                            aiid = method.get("aiid")
                            name = method.get("name", "Unknown")
                            print(f"\n[{siid}:{aiid}] {name}")

        else:
            print(f"[!] Error: {data.get('message', 'Unknown error')}")
    else:
        print(f"[!] HTTP Error: {resp.status_code}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
