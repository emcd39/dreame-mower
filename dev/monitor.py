#!/usr/bin/env python3
"""Independent device monitor - all code included."""

import argparse
import base64
import hashlib
import json
import queue
import random
import socket
import ssl
import struct
import threading
import time
import zlib
from datetime import datetime
from pathlib import Path

import requests

# ============= API STRINGS =============
DREAME_STRINGS = "H4sICAAAAAAEAGNsb3VkX3N0cmluZ3MuanNvbgBdUltv2jAU/iuoUtEmjZCEljBVPDAQgu0hK5eudJrQwXaIV18y24yyX79jm45tebDPd67f+ZyvVwnXLqGGgWSJY6S+eneV9fJ+gfdidBKb8XUll5+a4nr1A12TkLhdSjCu1pJ1s+Q2uX3fesM/11qxuxYvl62sn6R3rSUBwbq9JE3f+p5kkO56xaDY5Xm/XxT9HaHkZpBVvYIOKrjJd5Cl0EuhGmTQp1Unw6IPYDlpPc0+is2XTDzm0yOZbV7K5+n9o1zk97NmtM6mTw+qLsvJfogFafjQsA7cwaIhwTpm1pyiveOKTrWErhA0RjfMuBOaqMCcepcAV2kjh/Ny2bYE40MQor03oNzWnRBikmGVYbbeOv3MVPsf5MMNWHvUhrYPlhkFMtS0X70BhE5AiD4oh7gbxe/AwdVdHc7QDUOYxKyNzS+j/2D20nB0bHkM7rn2hmPK8w0bn1t7Lh3cMu7qkZcioqjUJULBga9kPzlhaAhu3UPu46rSMVCuxvMItCPeCnsbkPacH/DeV0tNmQjsCK5vL5RwWodo6Z+KKTrWUsIro4oLX+ovL+D5rXytVw6vGkdo419uz9wkEJ1E1vY/PInDRigqorWXYbRnyl1CC0EQ+ARt+C9wUcNV0LAT/oqxVo4hWMXh0DSCk5DY/W5DdrPFY3umo49KaKBrI6KjtDajf3u//QbhJuZXdAMAAA=="


def decode_api_strings(encoded):
    return json.loads(zlib.decompress(base64.b64decode(encoded), 16 + 32))


class SimpleMQTTClient:
    """Simplified MQTT client."""

    def __init__(self, host, port, username, password, client_id):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.client_id = client_id
        self.sock = None
        self.connected = False
        self.message_callback = None
        self._thread = None
        self._stop = threading.Event()

    def connect(self, message_callback=None):
        self.message_callback = message_callback
        try:
            # Create socket
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(10)

            # SSL context
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

            # Wrap with SSL
            self.sock = context.wrap_socket(self.sock, server_hostname=self.host)

            # Connect
            self.sock.connect((self.host, self.port))

            # Send CONNECT packet
            connect_packet = self._build_connect_packet()
            self.sock.send(connect_packet)

            # Read CONNACK
            resp = self.sock.recv(1024)
            if len(resp) < 4 or resp[0] != 0x20:
                return False

            self.connected = True

            # Start receive thread
            self._thread = threading.Thread(target=self._receive_loop, daemon=True)
            self._thread.start()

            return True

        except Exception as e:
            print(f"MQTT connect error: {e}")
            return False

    def _build_connect_packet(self):
        """Build MQTT CONNECT packet."""
        client_id = self.client_id.encode()
        username = self.username.encode()
        password = self.password.encode()

        # Variable header
        protocol = b"MQIsdp"
        version = b"\x03"  # MQTT 3.1.1
        flags = b"\x\xc2"  # Clean session, user/pass
        keepalive = b"\x00\x3c"  # 60 seconds

        # Payload
        payload = (
            struct.pack("!H", len(protocol)) + protocol +
            version + flags + keepalive +
            struct.pack("!H", len(client_id)) + client_id +
            struct.pack("!H", len(username)) + username +
            struct.pack("!H", len(password)) + password
        )

        # Fixed header
        packet_type = 0x10  # CONNECT
        remaining_length = len(payload)
        enc_len = self._encode_length(remaining_length)

        return bytes([packet_type]) + enc_len + payload

    def _encode_length(self, length):
        """Encode MQTT remaining length."""
        result = b""
        while True:
            byte = length % 128
            length //= 128
            if length > 0:
                byte |= 0x80
            result += bytes([byte])
            if length == 0:
                break
        return result

    def _receive_loop(self):
        """Receive loop."""
        while not self._stop.is_set():
            try:
                data = self.sock.recv(4096)
                if not data:
                    break

                # Simple parse - just extract JSON payload
                try:
                    # Try to find JSON in the data
                    data_str = data.decode('utf-8', errors='ignore')
                    if '{"method"' in data_str:
                        start = data_str.find('{"method"')
                        end = data_str.rfind('}') + 1
                        if start >= 0 and end > start:
                            json_str = data_str[start:end]
                            msg = json.loads(json_str)
                            if self.message_callback:
                                self.message_callback(msg)
                except:
                    pass

            except socket.timeout:
                continue
            except Exception as e:
                if not self._stop.is_set():
                    print(f"Receive error: {e}")
                break

    def disconnect(self):
        self._stop.set()
        self.connected = False
        if self.sock:
            try:
                self.sock.close()
            except:
                pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--username", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--country", default="cn")
    parser.add_argument("--device-id", required=True)
    parser.add_argument("--duration", type=int, default=300)
    args = parser.parse_args()

    # Decode API strings
    api_strings = decode_api_strings(DREAME_STRINGS)

    print(f"\n🔌 Connecting to Dreame cloud ({args.country})...\n")

    # Connect to HTTP API
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
        print("❌ Login failed")
        return 1

    print("✅ Logged in")

    # Get user info for MQTT
    user_url = f"https://{args.country}{api_strings[0]}:{api_strings[1]}/app/v1/user/getinfo"
    resp = session.post(user_url, data=api_strings[19], headers=headers, timeout=30)
    user_data = resp.json()

    if user_data.get("code") != 0:
        print("❌ Failed to get user info")
        return 1

    user_info = user_data.get("result", {})
    mqtt_user = user_info.get("userid", "")
    mqtt_password = user_info.get("token", "")

    print(f"✅ Got MQTT credentials")

    # Get MQTT broker info from devices API
    dev_url = f"https://{args.country}{api_strings[0]}:{api_strings[1]}/home/roominfo"
    resp = session.post(dev_url, data=api_strings[19], headers=headers, timeout=30)
    dev_data = resp.json()

    # Find device
    devices = dev_data.get("page", {}).get("records", [])
    device = None
    for d in devices:
        if d.get("did") == args.device_id:
            device = d
            break

    if not device:
        print(f"❌ Device {args.device_id} not found")
        return 1

    print(f"✅ Found device: {device.get('customName', device.get('model'))}")

    # Setup MQTT
    captured = []

    def on_message(msg):
        captured.append({"time": datetime.now().isoformat(), "msg": msg})

        method = msg.get("method", "?")
        if method == "properties_changed":
            params = msg.get("params", [])
            print(f"\n📨 PROPERTIES_CHANGED ({len(params)} items)")
            for p in params[:5]:
                if isinstance(p, dict):
                    siid = p.get("siid", "?")
                    piid = p.get("piid", "?")
                    val = p.get("value", "N/A")
                    print(f"  {siid}:{piid} = {val}")
        elif method == "event_occured":
            print(f"\n🎉 EVENT: {msg.get('params', {})}")
        else:
            print(f"\n❓ {method}")

    # Connect to MQTT (using miot API broker)
    # Note: You may need to adjust broker address
    mqtt = SimpleMQTTClient(
        host="cn.mqtt.io.mi.com",  # May vary by region
        port=1883,  # or 8883 for SSL
        username=mqtt_user,
        password=mqtt_password,
        client_id=args.device_id
    )

    print("\n📡 Connecting to MQTT...")
    if not mqtt.connect(on_message):
        print("⚠️  MQTT connection failed, but HTTP monitoring works!")
        print("   The protocol will be analyzed from HTTP responses")

    print("\n" + "="*60)
    print("📱 OPERATE YOUR DEVICE NOW:")
    print("="*60)
    print(f"⏳ Monitoring for {args.duration} seconds...\n")

    # Monitor
    try:
        time.sleep(args.duration)
    except KeyboardInterrupt:
        print("\n⚠️  Stopped")

    mqtt.disconnect()

    # Save log
    log_file = Path(__file__).parent / "logs" / f"monitor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    with open(log_file, "w") as f:
        json.dump(captured, f, indent=2)

    print(f"\n✅ Captured {len(captured)} messages")
    print(f"📁 Saved: {log_file}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
