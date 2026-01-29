#!/usr/bin/python3
import json
import requests
import os
import sys
import argparse
import difflib
import time
from requests.exceptions import Timeout, ConnectionError, HTTPError

BASE = "http://dl.8bitdo.com:8080"
URL_ROOT = BASE + "/firmware/select"

currentValidTypes = {
    "NGC Modkit": 91,
    "Ultimate 2C Bluetooth": 96,
    "NGC Adapter": 92,
    "Saturn Adapter": 99,
    "Ultimate MG": 100,
    "Ultimate MGX": 79,
    "M30 Wired for Xbox": 69,
    "Ultimate C Bluetooth": 66,
    "Mirco": 60,
    "Retro Receiver for PS": 59,
    "NEOGEO": 57,
    "Arcade Stick for Xbox": 51,
    "N64 Modkit": 53,
    "Ultimate C": 48,
    "Ultimate C Wired": 50,
    "Ultimate 2.4g": 43,
    "Ultimate 2.4g Adapter": 44,
    "Ultimate": 42,
    "Ultimate Adapter": 42,
    "Ultimate Wired": 45,
    "Lite 2": 47,
    "Lite SE": 46,
    "Ultimate for Xbox": 40,
    "Pro 2 Wired": 37,
    "USB Adapter 2": 39,
    "Pro 2 for Xbox": 37,
    "Pro 2": 33,
    "Arcade Stick": 34,
    "Arcade Stick Receiver": 35,
    "SN30 Pro for Android": 31,
    "Zero 2 gamepad": 29,
    "Lite gamepad": 28,
    "S30 Modkit": 27,
    "Dogbone Modkit": 26,
    "SN30 Plus +": 25,
    "Retro Receiver for MD/Genesis": 21,
    "M30": 22,
    "GBros. Apdater": 20,
    "N30 Pro 2": 19,
    "SF30 Pro": 9,
    "N30 Arcade Stick": 4,
    "FC30 Pro": 13,
    "F30": 2,
    "N30": 18,
    "SN30": 17,
    "SF30": 3,
    "N64": 10,
    "F30 Arcade Stick": 5,
    "USB Apdater": 8,
    "Classic RR": 6,
    "NES RR": 7,
    "SFC RR": 7,
    "P30 Modkit": 24,
    "SN30 Modkit": 16,
    "N30 Modkit": 15,
    "M30 Modkit": 14,
    "USB Apdater for PS classic": 8
}


# ----------------------------
# Retry helper
# ----------------------------

def request_with_retry(method, url, *, max_retries=5, backoff=1, **kwargs):
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.request(method, url, **kwargs)

            if response.status_code >= 500:
                raise HTTPError(
                    f"Server error: {response.status_code}",
                    response=response
                )

            return response

        except (Timeout, ConnectionError, HTTPError) as e:
            if attempt == max_retries:
                print(f"Request failed after {max_retries} attempts.")
                raise

            delay = backoff * (2 ** (attempt - 1))
            print(
                f"Request failed ({type(e).__name__}), "
                f"retrying in {delay}s... [{attempt}/{max_retries}]"
            )
            time.sleep(delay)


# ----------------------------
# Argparse
# ----------------------------

def parse_args():
    parser = argparse.ArgumentParser(
        description="firmware downloader (non-interactive)"
    )

    parser.add_argument(
        "--list-devices",
        action="store_true",
        help="List supported devices and exit"
    )

    parser.add_argument(
        "--device",
        help="Device name (fuzzy-matched)"
    )

    parser.add_argument(
        "--list-firmware",
        action="store_true",
        help="List available firmware versions for device"
    )

    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--latest",
        action="store_true",
        help="Download latest firmware (default)"
    )
    group.add_argument(
        "--firmware",
        type=int,
        help="Download firmware by index (from --list-firmware)"
    )

    return parser.parse_args()


# ----------------------------
# Device handling
# ----------------------------

def list_devices():
    for name, t in currentValidTypes.items():
        print(f"{name} (Type {t})")


def resolve_device(name: str):
    keys = list(currentValidTypes.keys())

    # Exact
    if name in currentValidTypes:
        return name, currentValidTypes[name]

    # Case-insensitive
    lower_map = {k.lower(): k for k in keys}
    if name.lower() in lower_map:
        k = lower_map[name.lower()]
        return k, currentValidTypes[k]

    # Partial
    partial = [k for k in keys if name.lower() in k.lower()]
    if len(partial) == 1:
        k = partial[0]
        return k, currentValidTypes[k]

    # Fuzzy
    matches = difflib.get_close_matches(name, keys, n=3, cutoff=0.6)
    if matches:
        print("Device not found. Did you mean:")
        for m in matches:
            print(f"  - {m}")
    else:
        print("Device not found. Use --list-devices to see valid names.")

    sys.exit(1)


# ----------------------------
# Firmware API
# ----------------------------

def fetch_firmware(device_type):
    headers = {
        "Type": str(device_type),
        "Beta": "1"
    }

    try:
        response = request_with_retry(
            "POST",
            URL_ROOT,
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
    except Exception as e:
        print(f"API request failed: {e}")
        sys.exit(1)

    try:
        payload = response.json()
    except json.JSONDecodeError:
        print("API returned invalid JSON.")
        sys.exit(1)

    if "list" not in payload or not isinstance(payload["list"], list):
        print("Unexpected API response format.")
        sys.exit(1)

    firmwares = []
    for fw in payload["list"]:
        if isinstance(fw, str):
            try:
                fw = json.loads(fw)
            except json.JSONDecodeError:
                continue
        if isinstance(fw, dict):
            firmwares.append(fw)

    if not firmwares:
        print("Firmware list is empty.")
        sys.exit(1)

    firmwares.sort(key=lambda fw: fw.get("date", 0), reverse=True)
    return firmwares


# ----------------------------
# Download
# ----------------------------

def download(url: str, file_name: str):
    try:
        response = request_with_retry(
            "GET",
            url,
            stream=True,
            timeout=15
        )
        response.raise_for_status()
    except Exception as e:
        print(f"Download failed: {e}")
        sys.exit(1)

    length = response.headers.get("content-length")
    block_size = 1_000_000

    if length:
        length = int(length)
        block_size = max(4096, length // 20)

    with open(file_name, "wb") as f:
        size = 0
        for chunk in response.iter_content(block_size):
            if not chunk:
                break
            f.write(chunk)
            size += len(chunk)
            if length:
                percent = int((size / length) * 100)
                print(f"Downloading: {percent}%", end="\r")

    print("\nDownload complete.")


# ----------------------------
# Main
# ----------------------------

def main():
    args = parse_args()

    if args.list_devices:
        list_devices()
        return

    if not args.device:
        print("Error: --device is required (unless --list-devices)")
        sys.exit(1)

    device_name, device_type = resolve_device(args.device)
    firmwares = fetch_firmware(device_type)

    if args.list_firmware:
        for i, fw in enumerate(firmwares, start=1):
            print(f"{i:2}. {fw['fileName']} ({fw['date']})")
        return

    if args.firmware:
        index = args.firmware - 1
        if index < 0 or index >= len(firmwares):
            print("Invalid firmware index.")
            sys.exit(1)
        selected_fw = firmwares[index]
        print(
            f"Downloading firmware for {device_name}: "
            f"{selected_fw['fileName']} ({selected_fw['date']})"
        )
    else:
        selected_fw = firmwares[0]  # latest
        print(
            f"Downloading firmware for {device_name}: "
            f"{selected_fw['fileName']} ({selected_fw['date']}) [LATEST]"
        )



    fw_dir = os.path.join(os.getcwd(), "fw", device_name)
    os.makedirs(fw_dir, exist_ok=True)

    file_url = BASE + selected_fw["filePathName"]
    file_name = selected_fw["fileName"].replace(" ", "_").replace("/", "-")
    file_date = selected_fw["date"]

    out_path = os.path.join(fw_dir, f"{file_name}_{file_date}.dat")
    print(f"Saving to: {out_path}")
    download(file_url, out_path)
    print(f"Saved to: {out_path}")


if __name__ == "__main__":
    main()
