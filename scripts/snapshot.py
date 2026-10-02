"""Save the emulator's current screen as a PNG (for inspection; never commit the output).

uv run python scripts/snapshot.py out.png --scale 0.5
"""

from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np

from hsai.emulator import connect, controller, find_emulator
from hsai.emulator._proto import emulator_controller_pb2 as pb


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--scale", type=float, default=1.0, help="resize factor for the output")
    parser.add_argument("--avd", default=None, help="AVD name when several emulators run")
    args = parser.parse_args()

    stub = controller(connect(find_emulator(args.avd)))
    image = stub.getScreenshot(pb.ImageFormat(format=pb.ImageFormat.RGB888))
    height, width = image.format.height, image.format.width
    pixels = np.frombuffer(image.image, dtype=np.uint8).reshape(height, width, 3)
    if args.scale != 1.0:
        size = (round(width * args.scale), round(height * args.scale))
        pixels = cv2.resize(pixels, size, interpolation=cv2.INTER_AREA)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(args.output), cv2.cvtColor(pixels, cv2.COLOR_RGB2BGR))
    print(f"{args.output} ({width}x{height} -> {pixels.shape[1]}x{pixels.shape[0]})")


if __name__ == "__main__":
    main()
