#!/usr/bin/env python3
"""Simple device status monitor - polls device via HTTP API."""

import argparse
import base64
import hashlib
import json
import re
import time
import zlib
from datetime import datetime
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
    parser.add_argument("--duration", type=int, default=300)
    parser.add_argument("--interval", type=int, default=5)
    args = parser.parse_args()

    # Load API strings from original file
    api_strings = load_api_strings()

    print(f"\n[*] Connecting to Dreame cloud ({args.country})...")
    print(f"[+] Device ID: {args.device_id}")
    print(f"[*] Polling every {args.interval}s for {args.duration}s\n")

    # Setup session
    session = requests.Session()

    # Login
    login_data = (f"{api_strings[12]}{api_strings[14]}"
                 f"{args.username}{api_strings[15]}"
                 f"{hashlib.md5((args.password + api_strings[2]).encode()).hexdigest()}"
                 f"{api_strings[16]}")

    headers = {
        "Accept": "*/*",
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": api_strings[11],
    }

    url = f"https://{args.country}{api_strings[0]}:{api_strings[1]}/app/v1/login"
    resp = session.post(url, data=login_data, headers=headers, timeout=30)

    if resp.status_code != 200 or resp.json().get("code") != 0:
        print("[!] Login failed")
        return 1

    print("[+] Logged in\n")

    # Get devices list to find the device
    dev_url = f"https://{args.country}{api_strings[0]}:{api_strings[1]}/home/roominfo"
    resp = session.post(dev_url, data=api_strings[19], headers=headers, timeout=30)
    dev_data = resp.json()

    devices = dev_data.get("page", {}).get("records", [])
    target_device = None
    for d in devices:
        if d.get("did") == args.device_id:
            target_device = d
            break

    if not target_device:
        print(f"[!] Device {args.device_id} not found")
        return 1

    print(f"[+] Found: {target_device.get('customName', 'Unknown')}")
    print(f"   Model: {target_device.get('model')}")
    print(f"   Online: {target_device.get('online')}")
    print(f"   Battery: {target_device.get('battery')}%")
    print(f"   Status: {target_device.get('latestStatus')}")
    print()

    print("="*60)
    print("[*] OPERATE YOUR DEVICE NOW!")
    print("   Watch the status changes below:")
    print("="*60)
    print()

    # Poll for changes
    captured = []
    last_battery = target_device.get('battery')
    last_status = target_device.get('latestStatus')

    try:
        start_time = time.time()
        poll_count = 0

        while time.time() - start_time < args.duration:
            time.sleep(args.interval)
            poll_count += 1

            # Refresh device list
            resp = session.post(dev_url, data=api_strings[19], headers=headers, timeout=30)
            dev_data = resp.json()

            devices = dev_data.get("page", {}).get("records", [])
            for d in devices:
                if d.get("did") == args.device_id:
                    target_device = d
                    break

            # Get current state
            battery = target_device.get('battery')
            status = target_device.get('latestStatus')
            online = target_device.get('online')

            # Check for changes
            changes = []
            if battery != last_battery:
                changes.append(f"Battery: {last_battery}% → {battery}%")
                last_battery = battery

            if status != last_status:
                changes.append(f"Status: {last_status} → {status}")
                last_status = status

            if changes:
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"[{timestamp}] {' | '.join(changes)}")

                # Capture
                captured.append({
                    "time": datetime.now().isoformat(),
                    "battery": battery,
                    "status": status,
                    "online": online,
                    "raw": target_device
                })

    except KeyboardInterrupt:
        print("\n[WARN]  Stopped by user")

    # Summary
    print()
    print("="*60)
    print(f"[+] Polled {poll_count} times")
    print(f"[STAT] Captured {len(captured)} state changes")
    print()

    # Save log
    log_dir = Path(__file__).parent / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"poll_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    with open(log_file, "w") as f:
        json.dump(captured, f, indent=2)

    print(f"[FILE] Log saved: {log_file}")

    # Show status codes seen
    if captured:
        print("\n[LIST] Status codes seen:")
        for c in captured:
            print(f"   Status {c['status']} (Battery: {c['battery']}%) - {c['time']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
