import os
import struct

ROOT = os.path.dirname(__file__)
PNG_PATH = os.path.join(ROOT, "icons", "icon.png")
ICO_PATH = os.path.join(ROOT, "icons", "icon.ico")

if not os.path.exists(PNG_PATH):
    raise SystemExit(f"input PNG not found: {PNG_PATH}")

with open(PNG_PATH, "rb") as f:
    png = f.read()

# ICO header (ICONDIR)
# 2 bytes reserved, 2 bytes type (1 for icon), 2 bytes count
icondir = struct.pack("<3H", 0, 1, 1)

# ICONDIRENTRY (16 bytes):
# BYTE width, BYTE height, BYTE colorCount, BYTE reserved,
# WORD planes, WORD bitCount, DWORD bytesInRes, DWORD imageOffset
# Use 0 for width/height to indicate 256, and embed PNG data as image
width = 0
height = 0
colorCount = 0
reserved = 0
planes = 1
bitcount = 32
bytes_in_res = len(png)
image_offset = 6 + 16  # header + one entry
entry = struct.pack("<BBBBHHII", width, height, colorCount, reserved, planes, bitcount, bytes_in_res, image_offset)

with open(ICO_PATH, "wb") as f:
    f.write(icondir)
    f.write(entry)
    f.write(png)

print("Wrote ico:", ICO_PATH)
