#!/usr/bin/python3
import json
import requests
import os
import sys
import argparse

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
    "8BitDo Ultimate C Bluetooth": 66,
    "8BitDo Mirco": 60,
    "8BitDo Retro Receiver for PS": 59,
    "8BitDo NEOGEO": 57,
    "8BitDo Arcade Stick for Xbox": 51,
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
    "8BitDo Ultimate for Xbox": 40,
    "8BitDo Pro 2 Wired": 37,
    "8BitDo USB Adapter 2": 39,
    "8BitDo Pro 2 for Xbox": 37,
    "8BitDo Pro 2": 33,
    "8BitDo Arcade Stick": 34,
    "8BitDo Arcade Stick Receiver": 35,
    "8BitDo SN30 Pro for Android": 31,
    "8BitDo Zero 2 gamepad": 29,
    "8BitDo Lite gamepad": 28,
    "8BitDo S30 Modkit": 27,
    "8BitDo Dogbone Modkit": 26,
    "8BitDo SN30 Plus +": 25,
    "Retro Receiver for MD/Genesis": 21,
    "8BitDo M30": 22,
    "8BitDo GBros. Apdater": 20,
    "8BitDo N30 Pro 2": 19,
    "8Bitdo SF30 Pro": 9,
    "8Bitdo N30 Arcade Stick": 4,
    "8Bitdo FC30 Pro": 13,
    "8Bitdo F30": 2,
    "8Bitdo N30": 18,
    "8Bitdo SN30": 17,
    "8Bitdo SF30": 3,
    "8BitDo N64": 10,
    "8BitDo F30 Arcade Stick": 5,
    "8BitDo USB Apdater": 8,
    "8BitDo Classic RR": 6,
    "8BitDo NES RR": 7,
    "8BitDo SFC RR": 7,
    "8BitDo P30 Modkit": 24,
    "8BitDo SN30 Modkit": 16,
    "8BitDo N30 Modkit": 15,
    "8BitDo M30 Modkit": 14,
    "8BitDo USB Apdater for PS classic": 8
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="8BitDo firmware downloader (non-interactive)"
    )

    parser.add_argument(
        "--list-devices",
        action="store_true",
        help="List supported devices and exit"
    )

    parser.add_argument(
        "--device",
        help="Device name (exact match from --list-devices)"
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


def list_devices():
    for name, t in currentValidTypes.items():
        print(f"{name} (Type {t})")


def fetch_firmware(device_type):
    headers = {
        "Type": str(device_type),
        "Beta": "1"
    }

    response = requests.post(URL_ROOT, headers=headers)
    response.raise_for_status()

    raw = response.json()["list"]
    firmwares = []

    for fw in raw:
        if isinstance(fw, str):
            fw = json.loads(fw)
        firmwares.append(fw)

    firmwares.sort(key=lambda fw: fw.get("date", 0), reverse=True)
    return firmwares


def download(url: str, file_name: str):
    response = requests.get(url, stream=True)
    response.raise_for_status()

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


def main():
    args = parse_args()

    if args.list_devices:
        list_devices()
        return

    if not args.device:
        print("Error: --device is required (unless --list-devices)")
        sys.exit(1)

    if args.device not in currentValidTypes:
        print("Unknown device. Use --list-devices to see valid names.")
        sys.exit(1)

    device_type = currentValidTypes[args.device]
    firmwares = fetch_firmware(device_type)

    if not firmwares:
        print("No firmware found.")
        return

    if args.list_firmware:
        for i, fw in enumerate(firmwares, start=1):
            print(f"{i:2}. {fw['fileName']} ({fw['date']})")
        return

    # Default behavior: latest
    if args.firmware:
        index = args.firmware - 1
        if index < 0 or index >= len(firmwares):
            print("Invalid firmware index.")
            sys.exit(1)
        selected_fw = firmwares[index]
    else:
        selected_fw = firmwares[0]

    fw_dir = os.path.join(os.getcwd(), "fw", args.device)
    os.makedirs(fw_dir, exist_ok=True)

    file_url = BASE + selected_fw["filePathName"]
    file_name = selected_fw["fileName"].replace(" ", "_").replace("/", "-")
    file_date = selected_fw["date"]

    out_path = os.path.join(fw_dir, f"{file_name}_{file_date}.dat")
    download(file_url, out_path)


if __name__ == "__main__":
    main()
