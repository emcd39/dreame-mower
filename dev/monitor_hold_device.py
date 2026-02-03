#!/usr/bin/env python3
"""Protocol monitor for Dreame hold devices (floor washers)."""

import argparse
import getpass
import json
import sys
import time
from datetime import datetime
from pathlib import Path
import importlib.util

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "custom_components"))

def load_cloud_modules():
    """Load cloud modules bypassing __init__.py."""

    # Create synthetic module hierarchy
    sys.modules["dreame_mower"] = type(sys)("dreame_mower")
    sys.modules["dreame_mower.dreame"] = type(sys)("dreame_mower.dreame")
    sys.modules["dreame_mower.dreame.cloud"] = type(sys)("dreame_mower.dreame.cloud")

    # Load const first (cloud_device needs it)
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


def main():
    parser = argparse.ArgumentParser(description="Monitor Dreame hold device")
    parser.add_argument("--username", help="Cloud username")
    parser.add_argument("--password", help="Cloud password")
    parser.add_argument("--country", default="cn", help="Cloud country")
    parser.add_argument("--device-id", required=True, help="Device ID")
    parser.add_argument("--duration", type=int, default=300, help="Duration in seconds")
    args = parser.parse_args()

    # Get credentials
    if not args.username:
        args.username = input("Enter username: ")
    if not args.password:
        args.password = getpass.getpass("Enter password: ")

    print(f"\n🔌 Connecting...")
    print(f"📍 Device ID: {args.device_id}\n")

    # Load modules
    cloud_device = load_cloud_modules()

    # Create device
    device = cloud_device.DreameMowerCloudDevice(
        username=args.username,
        password=args.password,
        country=args.country,
        account_type="dreame",
        device_id=args.device_id,
    )

    # Connect API
    if not device._cloud_base.connect():
        print("❌ API connection failed")
        return 1
    print("✅ API connected")

    # Setup callbacks
    messages = []

    def on_message(data):
        messages.append({"time": datetime.now().isoformat(), "data": data})
        method = data.get("method", "?")

        if method == "properties_changed":
            params = data.get("params", [])
            print(f"\n📨 PROPERTIES_CHANGED ({len(params)} items)")
            for p in params[:5]:
                if isinstance(p, dict) and "siid" in p:
                    print(f"  {p.get('siid')}:{p.get('piid')} = {p.get('value', 'N/A')}")

        elif method == "event_occured":
            print(f"\n🎉 EVENT: {data.get('params', {})}")

        elif method == "props":
            print(f"\n📋 PROPS: {list(data.get('params', {}).keys())[:5]}")

    def on_connected():
        print("\n✅ ✅ MQTT CONNECTED ✅")
        print("\n" + "="*60)
        print("📱 OPERATE YOUR DEVICE NOW:")
        print("="*60)
        print(f"⏳ Monitoring {args.duration}s...\n")

    def on_disconnected():
        print("\n⚠️  MQTT disconnected")

    # Connect MQTT
    print("📡 Connecting MQTT...")
    if not device.connect(
        message_callback=on_message,
        connected_callback=on_connected,
        disconnected_callback=on_disconnected
    ):
        print("❌ MQTT failed")
        return 1

    # Monitor
    try:
        time.sleep(args.duration)
    except KeyboardInterrupt:
        print("\n⚠️  Stopped")

    device.disconnect()

    # Save log
    log_dir = project_root / "dev" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"hold_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(messages, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Captured {len(messages)} messages")
    print(f"📁 {log_file}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
