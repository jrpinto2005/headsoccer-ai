"""F0 spike: latency from injecting a touch to seeing it on screen.

Android's "show taps" overlay draws a dot under every touch as soon as the system receives
it, so the first captured frame where the dot appears bounds the input path plus display
and capture, without any app-specific processing.

Run it on a static screen whose tapped area does nothing (empty launcher wallpaper), with
the device in portrait so touch and image coordinates coincide:

    uv run python scripts/spikes/touch_latency.py --trials 50
"""

from __future__ import annotations

import argparse
import subprocess
import threading
import time
from collections import deque
from pathlib import Path

import numpy as np

from hsai.emulator import Frame, ScreenStream, TouchInjector, connect, controller, find_emulator
from hsai.emulator.device import orientation

ADB = Path.home() / "Library/Android/sdk/platform-tools/adb"
PATCH = 24  # half-size of the patch inspected around the touch point, in pixels
DIFF_THRESHOLD = 25.0  # mean absolute difference that counts as "dot visible"


class FrameBuffer:
    """Consumes the screen stream on a background thread and keeps recent frames."""

    def __init__(self, stream: ScreenStream) -> None:
        self._frames: deque[Frame] = deque(maxlen=240)
        self._lock = threading.Lock()
        self._thread = threading.Thread(target=self._run, args=(stream,), daemon=True)
        self._thread.start()

    def _run(self, stream: ScreenStream) -> None:
        for frame in stream:
            with self._lock:
                self._frames.append(frame)

    def latest(self) -> Frame | None:
        with self._lock:
            return self._frames[-1] if self._frames else None

    def first_after(self, t_ns: int, predicate, timeout_s: float) -> Frame | None:  # type: ignore[no-untyped-def]
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            with self._lock:
                candidates = [f for f in self._frames if f.received_ns > t_ns]
            for frame in candidates:
                if predicate(frame):
                    return frame
            time.sleep(0.001)
        return None


def patch(frame: Frame, x: int, y: int) -> np.ndarray:
    return frame.pixels[y - PATCH : y + PATCH, x - PATCH : x + PATCH].astype(np.float32)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trials", type=int, default=50)
    parser.add_argument("--x-range", type=int, nargs=2, default=(300, 780))
    parser.add_argument("--y-range", type=int, nargs=2, default=(700, 1200))
    args = parser.parse_args()

    stub = controller(connect(find_emulator()))
    if orientation(stub) != "portrait":
        raise SystemExit("Rotate the device to portrait so touch and image coordinates match.")

    subprocess.run([ADB, "shell", "settings", "put", "system", "show_touches", "1"], check=True)
    rng = np.random.default_rng(0)
    to_display_ms: list[float] = []
    to_capture_ms: list[float] = []
    misses = 0
    try:
        with ScreenStream(stub) as stream, TouchInjector(stub) as touch:
            frames = FrameBuffer(stream)
            time.sleep(1.0)
            for _ in range(args.trials):
                x = int(rng.integers(*args.x_range))
                y = int(rng.integers(*args.y_range))
                baseline = frames.latest()
                if baseline is None:
                    raise SystemExit("No frames received; is the screen on?")
                reference = patch(baseline, x, y)

                def dot_visible(frame: Frame, x: int = x, y: int = y, ref=reference) -> bool:  # type: ignore[no-untyped-def]
                    return float(np.abs(patch(frame, x, y) - ref).mean()) > DIFF_THRESHOLD

                t0 = time.time_ns()
                touch.press(0, x, y)
                seen = frames.first_after(t0, dot_visible, timeout_s=1.0)
                time.sleep(0.05)
                touch.release(0)
                if seen is None:
                    misses += 1
                else:
                    to_display_ms.append((seen.produced_us * 1_000 - t0) / 1e6)
                    to_capture_ms.append((seen.received_ns - t0) / 1e6)
                time.sleep(0.4)  # let the dot fade before the next trial
    finally:
        subprocess.run([ADB, "shell", "settings", "put", "system", "show_touches", "0"], check=True)

    def summary(values: list[float]) -> str:
        if not values:
            return "-"
        a = np.asarray(values)
        return " / ".join(f"{np.percentile(a, q):.1f}" for q in (50, 95, 99))

    print(f"trials={args.trials} detected={len(to_display_ms)} misses={misses}")
    print(f"inject -> frame produced (ms, p50/p95/p99): {summary(to_display_ms)}")
    print(f"inject -> frame received (ms, p50/p95/p99): {summary(to_capture_ms)}")


if __name__ == "__main__":
    main()
