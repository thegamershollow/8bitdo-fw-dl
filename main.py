#!/usr/bin/python3
import json
import requests


def download(url: str, fileName: str):
    response = requests.get(url, stream=True)
    response.raise_for_status()
    length = response.headers.get('content-length')
    block_size = 1000000  # default value
    if length:
        length = int(length)
        block_size = max(4096, length // 20)
    #filesize = length*10**-6
    #filesize = round(filesize, 2)
    #print(f"{fileName} size: {filesize} MB")
    with open(fileName, 'wb') as f:
        size = 0
        for buffer in response.iter_content(block_size):
            if not buffer:
                break
            f.write(buffer)
            size += len(buffer)
            if length:
                percent = int((size / length) * 100)
                print(f"Downloading {fileName}: {percent}%", end='\r')
    print(f"\nDone Downloading {fileName}")



urlRoot = "http://dl.8bitdo.com:8080/firmware/select"

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

# Deduplicate type values
type_values = set(currentValidTypes.values())

for t in type_values:
    headers = {
        "Type": str(t),
        "Beta": "1"
    }

    try:
        response = requests.post(urlRoot, headers=headers)
        print(f"\nType {t}: Status {response.status_code}")
    except requests.RequestException as e:
        print(f"Request failed for Type {t}: {e}")
        continue

    # Try parsing the JSON safely
    try:
        data = response.json()["list"]
    except json.JSONDecodeError:
        print("Response is not valid JSON!")
        print(response.text)
        continue

    # Handle case where each item in the list is itself a JSON string
    firmwares = []
    for fw in data:
        if isinstance(fw, str):
            try:
                fw = json.loads(fw)
            except json.JSONDecodeError:
                #print(f"Skipping invalid JSON item: {fw}") # for debuging
                continue
        firmwares.append(fw)

    # Print firmware info
    for fw in firmwares:
        version = fw.get("version")
        file_url = fw.get("filePathName")
        #print(f"Version: {version}, File: {file_url}") # for debuging
        