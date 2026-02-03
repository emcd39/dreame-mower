"""Standalone device lister without triggering Home Assistant imports."""

import argparse
import base64
import getpass
import hashlib
import json
import random
import requests
import zlib
from typing import Any, List, Optional

# API strings - directly from cloud_base.py
DREAME_STRINGS = "H4sICAAAAAAEAGNsb3VkX3N0cmluZ3MuanNvbgBdUltv2jAU/iuoUtEmjZCEljBVPDAQgu0hK5eudJrQwXaIV18y24yyX79jm45tebDPd67f+ZyvVwnXLqGGgWSJY6S+eneV9fJ+gfdidBKb8XUll5+a4nr1A12TkLhdSjCu1pJ1s+Q2uX3fesM/11qxuxYvl62sn6R3rSUBwbq9JE3f+p5kkO56xaDY5Xm/XxT9HaHkZpBVvYIOKrjJd5Cl0EuhGmTQp1Unw6IPYDlpPc0+is2XTDzm0yOZbV7K5+n9o1zk97NmtM6mTw+qLsvJfogFafjQsA7cwaIhwTpm1pyiveOKTrWUsIro4oLX+ovL+D5rXytVw6vGkdo419uz9wkEJ1E1vY/PInDRigqorWXYbRnyl1CC0EQ+ARt+C9wUcNV0LAT/oqxVo4hWMXh0DSCk5DY/W5DdrPFY3umo49KaKBrI6KjtDajf3u//QbhJuZXdAMAAA=="
MOVA_STRINGS = "H4sIAAAAAAAAA11Sa2/aMBT9K6hS0SYtIQktYar6gYEQ3TRlLdC1nabo4jjEqx+ZbUrZr5+vY7p2+eDcc+772D9OYqZsLNQTRJaSJiZKnHzonaTDbJSjcTM58PvpaS2WX9r8dPUbua8uulwK0LZRgg7S+Dw+/9h7x741StKLHiuWvXQUJxe9JQFOB8M4Sd77omScbIb5ON9k2WiU56MNqcjZOK2HeTWu4SzbQJrAMIF6nMKoqqMUsz6BYaT3sPjM77+n/C6b78ni/rl4nF/fiZvsetFO1un84VY2RTHbXmJGgl+GlrFgdwYtAcZSvWYVgg2T1UwJYBJRq1VLtT2g7cS48iEtB1srLS6vimXfEBdxCZz3txqkLe3BQYzStNbUNKVVj1T23yDvb8GYvdJVf2eoliC6rP6R7pCvBoSonbRIDCpNXWgEO9sMlD99RfS5MGpM+YLftESCPrfMMSUL7i1T3rJU4uTd/qEBDhW5jcPiCFGZAP9pF3wVWPDZ9IkRihZnxt56oZmsVfAVq+lVQMqSo9mCBmGOSR2z9UWEqijvhiVOE/NqQNc4Cg/SUFlNlRDwMl/NuM/HP0p7vEpfADXFf+OaKe2vdkvtzE8+C3uY/4lZ13XiFEe4RnkmW9rdSnDecIIIY5Rmf8AGfVde36h7PFMlnd42WoUpoG05Iz528Mt0CW2JZ3mcTO0lV1CtNQ9MYUxavaZ//gW/B6/rrAMAAA=="


def decode_api_strings(encoded: str) -> List[str]:
    """Decode compressed and base64-encoded API strings."""
    return json.loads(zlib.decompress(base64.b64decode(encoded), 16 + 32))


class SimpleCloudClient:
    """Simplified Dreame cloud API client."""

    def __init__(self, username: str, password: str, country: str, account_type: str):
        if account_type == "dreame":
            self.api_strings = decode_api_strings(DREAME_STRINGS)
        elif account_type == "mova":
            self.api_strings = decode_api_strings(MOVA_STRINGS)
        else:
            raise ValueError(f"Unsupported account_type: {account_type}")

        self.username = username
        self.password = password
        self.country = country
        self.session = None
        self.logged_in = False

    def connect(self) -> bool:
        """Connect to cloud service."""
        try:
            self.session = requests.Session()

            # Build login data
            data = (f"{self.api_strings[12]}{self.api_strings[14]}"
                   f"{self.username}{self.api_strings[15]}"
                   f"{hashlib.md5((self.password + self.api_strings[2]).encode()).hexdigest()}"
                   f"{self.api_strings[16]}")

            headers = {
                "Accept": "*/*",
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept-Language": "en-US;q=0.8",
                "User-Agent": self.api_strings[11],
            }

            url = f"https://{self.country}{self.api_strings[0]}:{self.api_strings[1]}/app/v1/login"

            response = self.session.post(url, data=data, headers=headers, timeout=30)

            if response.status_code != 200:
                print(f"Login failed with status code: {response.status_code}")
                return False

            result = response.json()
            if result.get("code") != 0:
                print(f"Login failed with code: {result.get('code')}")
                print(f"Message: {result.get('message', 'Unknown error')}")
                return False

            self.logged_in = True
            return True

        except Exception as e:
            print(f"Connection error: {e}")
            import traceback
            traceback.print_exc()
            return False

    def get_devices(self) -> Optional[dict]:
        """Get list of devices."""
        if not self.logged_in:
            return None

        try:
            headers = {
                "Accept": "*/*",
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": self.api_strings[11],
            }

            url = f"https://{self.country}{self.api_strings[0]}:{self.api_strings[1]}/home/roominfo"

            response = self.session.post(url, data=self.api_strings[19], headers=headers, timeout=30)

            if response.status_code != 200:
                print(f"Failed to get devices: HTTP {response.status_code}")
                return None

            return response.json()

        except Exception as e:
            print(f"Error fetching devices: {e}")
            import traceback
            traceback.print_exc()
            return None


def main():
    parser = argparse.ArgumentParser(description="List Dreame devices")
    parser.add_argument("--username", help="Cloud username (email)")
    parser.add_argument("--password", help="Cloud password")
    parser.add_argument("--country", help="Cloud country code (cn, eu, us, ru, sg)")
    parser.add_argument("--account-type", default="dreame", choices=["dreame", "mova"])
    args = parser.parse_args()

    # Get credentials
    if not args.username:
        args.username = input("Enter username (email): ")
    if not args.password:
        args.password = getpass.getpass("Enter password: ")
    if not args.country:
        country = input("Enter country code (cn, eu, us, ru, sg) [default: cn]: ").strip()
        args.country = country if country else "cn"

    print(f"\n🔌 Connecting to {args.account_type} cloud ({args.country})...\n")

    # Create client
    client = SimpleCloudClient(
        username=args.username,
        password=args.password,
        country=args.country,
        account_type=args.account_type,
    )

    # Connect
    if not client.connect():
        print("❌ Failed to connect")
        print("Check your credentials and country code")
        return 1

    print("✅ Connected!\n")

    # Get devices
    devices = client.get_devices()
    if not devices or "page" not in devices:
        print("❌ Failed to get devices")
        return 1

    records = devices["page"].get("records", [])
    if not records:
        print("No devices found")
        return 0

    print("=" * 70)
    print(f"📱 Found {len(records)} device(s):")
    print("=" * 70)

    for i, device in enumerate(records, 1):
        model = device.get("model", "unknown")
        did = device.get("did", "unknown")
        mac = device.get("mac", "unknown")
        custom_name = device.get("customName", "")
        display_name = device.get("deviceInfo", {}).get("displayName", "")

        print(f"\nDevice {i}:")
        print(f"  Model:    {model}")
        print(f"  Name:     {custom_name or display_name}")
        print(f"  DeviceID: {did}")
        print(f"  MAC:      {mac}")

        # Determine device type
        if model.startswith("dreame.mower.") or model.startswith("mova.mower."):
            print(f"  Type:     🟢 Lawn Mower (already supported)")
        elif model.startswith("dreame.vacuum.") or model.startswith("mova.vacuum."):
            print(f"  Type:     🔵 Vacuum/Wet-Dry Cleaner")
        else:
            print(f"  Type:     ❓ Unknown")

    print("\n" + "=" * 70)
    print("Full JSON:")
    print("=" * 70)
    print(json.dumps(devices, indent=2, ensure_ascii=False))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
