#!/usr/bin/env python3
"""Get MIoT spec for Dreame hold device."""

import json
import urllib.request

def get_miot_spec(model="dreame.hold.w2422"):
    """Get device spec from MIoT API."""

    # MIoT spec API endpoints
    apis = [
        f"https://miot-spec.org/m/deviceprops?type=device&model={model}",
        f"https://miot-spec.org/m/devicefunctions?type=device&model={model}",
        f"https://miot-spec.org/m/devicespec?type=device&model={model}",
    ]

    for api_url in apis:
        try:
            print(f"[*] Trying: {api_url}")
            req = urllib.request.Request(api_url)
            req.add_header('User-Agent', 'Mozilla/5.0')
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read())

                print("\n" + "="*60)
                print(f"SUCCESS: {api_url}")
                print("="*60)
                print(json.dumps(data, indent=2))
                print()

                return data
        except Exception as ex:
            print(f"[!] Failed: {ex}")
            continue

    return None

if __name__ == "__main__":
    result = get_miot_spec()
    if result:
        print("\n[+] Found spec data!")
    else:
        print("\n[!] No spec data found")
        print("[*] Try checking manually at:")
        print("    https://home.miot-spec.com/spec/dreame.hold.w2422")
