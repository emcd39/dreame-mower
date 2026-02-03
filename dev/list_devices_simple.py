"""Simple device lister without Home Assistant dependency."""

import argparse
import getpass
import json
import sys
import os

# Add parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from custom_components.dreame_mower.dreame.cloud.cloud_base import DreameMowerCloudBase

def main():
    parser = argparse.ArgumentParser(description="List Dreame devices for your account")
    parser.add_argument("--username", default=None, help="Cloud username (email)")
    parser.add_argument("--password", default=None, help="Cloud password")
    parser.add_argument("--country", default=None, help="Cloud country code (e.g. 'cn', 'eu', 'us', 'ru', 'sg')")
    parser.add_argument("--account-type", default="dreame", choices=["dreame", "mova"], help="Account type")
    args = parser.parse_args()

    # Prompt for username, password, country if not provided
    if args.username is None:
        args.username = input("Enter username (email): ")
    if args.password is None:
        args.password = getpass.getpass("Enter password: ")
    if args.country is None:
        print("No country provided, using default: eu")
        args.country = "eu"

    print(f"Connecting to {args.account_type} cloud ({args.country})...")

    # Create cloud base client
    cloud = DreameMowerCloudBase(
        username=args.username,
        password=args.password,
        country=args.country,
        account_type=args.account_type,
    )

    # Connect and get devices
    if not cloud.connect():
        print("Failed to connect to cloud service")
        print("Please check your credentials and try again")
        sys.exit(1)

    print("Connected successfully!")

    devices = cloud.get_devices()
    if not devices or "page" not in devices:
        print("No devices found or error fetching devices")
        sys.exit(1)

    records = devices["page"].get("records", [])
    if not records:
        print("No devices found in your account")
        sys.exit(0)

    print(f"\nFound {len(records)} device(s):\n")

    # Display devices in a readable format
    for i, device in enumerate(records, 1):
        model = device.get("model", "unknown")
        did = device.get("did", "unknown")
        mac = device.get("mac", "unknown")
        custom_name = device.get("customName", "")
        display_name = device.get("deviceInfo", {}).get("displayName", "")

        print(f"Device {i}:")
        print(f"  Model: {model}")
        print(f"  Name: {custom_name or display_name}")
        print(f"  Device ID: {did}")
        print(f"  MAC: {mac}")
        print()

    # Also print full JSON for reference
    print("=" * 60)
    print("Full JSON output:")
    print("=" * 60)
    print(json.dumps(devices, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
