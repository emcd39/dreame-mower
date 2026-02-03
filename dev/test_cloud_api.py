#!/usr/bin/env python3
"""Direct API testing for Dreame cloud."""

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
    parser = argparse.ArgumentParser(description="Test Dreame cloud API")
    parser.add_argument("--username", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--country", default="cn")
    parser.add_argument("--account-type", default="dreame", choices=["dreame", "mova"])
    parser.add_argument("--device-id", required=True)
    args = parser.parse_args()

    # Create cloud client
    cloud = cloud_base.DreameMowerCloudBase(
        username=args.username,
        password=args.password,
        country=args.country,
        account_type=args.account_type,
    )

    # Connect
    print("[*] Connecting...")
    if not cloud.connect():
        print("[!] Failed to connect")
        return 1

    print("[+] Connected!\n")

    api = cloud._api_strings

    # Try different API endpoints
    endpoints = [
        # Endpoint format: (path fragment, description, data_builder)
        (
            f"{api[23]}/{api[26]}/{api[44]}",
            "Get device data (properties)",
            lambda: {"did": args.device_id, api[35]: [{"did": args.device_id, "siid": 3, "piid": 1}]},
        ),
        (
            f"{api[23]}/{api[26]}/{api[45]}",
            "Set device data",
            lambda: {"did": args.device_id, api[35]: [{"did": args.device_id, "siid": 3, "piid": 1, "value": 1}]},
        ),
        (
            f"home/deviceprops",
            "Device properties (old endpoint)",
            lambda: {"did": args.device_id},
        ),
        (
            f"home/methodlist",
            "Method list (old endpoint)",
            lambda: {"did": args.device_id},
        ),
    ]

    for endpoint_path, description, data_builder in endpoints:
        print("="*60)
        print(f"Testing: {description}")
        print(f"Endpoint: {endpoint_path}")
        print()

        try:
            url = f"{cloud.get_api_url()}/{endpoint_path}"
            data = data_builder()

            print(f"URL: {url}")
            print(f"Data: {json.dumps(data, ensure_ascii=False)}")

            headers = {
                "Content-Type": "application/json",
                "User-Agent": api[3],
                api[46]: cloud._key,  # Add auth token
            }
            if args.country == "cn":
                headers[api[48]] = api[4]

            response = cloud._session.post(
                url,
                json=data,
                headers=headers,
                timeout=30
            )

            print(f"\nHTTP Status: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                print(f"Response code: {result.get('code')}")
                print(f"Response: {json.dumps(result, indent=2, ensure_ascii=False)[:1000]}...")

                if result.get("code") == 0:
                    print("\n[+] SUCCESS!")
            else:
                print(f"[!] HTTP Error: {response.text[:500]}")

        except Exception as ex:
            print(f"[!] Exception: {ex}")

        print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
