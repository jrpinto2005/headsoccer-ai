"""F0 spike: end-to-end input latency inside the game.

Head Soccer highlights an on-screen button as soon as it registers a touch on it. We inject
a press and look for the first captured frame where the button is highlighted. That interval
covers touch injection, the game's input handling and rendering, and frame capture: the full
loop the agent will live in.

Run it during a match (the player walks left and right in place):

    uv run python scripts/spikes/input_latency.py --trials 40
"""

from __future__ import annotations

import argparse
import threading
import time
from collections import deque

import numpy as np

from hsai.emulator import Frame, ScreenStream, TouchInjector, connect, controller, find_emulator
from hsai.emulator._proto import emulator_controller_pb2 as pb
from hsai.emulator.coords import TouchMapper

# Button centres in upright 1920x1080 frames (measured from screenshots of a match).
BUTTONS = {"L": (190, 994), "R": (480, 994)}
PATCH = 30  # half-size of the inspected patch, px
THRESHOLD = 20.0  # mean absolute RGB difference that counts as "highlighted"


class LatestFrames:
    def __init__(self, stream: ScreenStream) -> None:
        self._frames: deque[Frame] = deque(maxlen=120)
        self._lock = threading.Lock()
        threading.Thread(target=self._run, args=(stream,), daemon=True).start()

    def _run(self, stream: ScreenStream) -> None:
        for frame in stream:
            with self._lock:
                self._frames.append(frame)

    def latest(self) -> Frame | None:
        with self._lock:
            return self._frames[-1] if self._frames else None

    def after(self, t_ns: int) -> list[Frame]:
        with self._lock:
            return [f for f in self._frames if f.received_ns > t_ns]


def patch(frame: Frame, x: int, y: int) -> np.ndarray:
    return frame.pixels[y - PATCH : y + PATCH, x - PATCH : x + PATCH].astype(np.float32)


def wait_for(frames: LatestFrames, since_ns: int, x: int, y: int, ref: np.ndarray, changed: bool,
             timeout_s: float = 1.0) -> Frame | None:  # fmt: skip
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        for frame in frames.after(since_ns):
            diff = float(np.abs(patch(frame, x, y) - ref).mean())
            if (diff > THRESHOLD) == changed:
                return frame
        time.sleep(0.001)
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trials", type=int, default=40)
    args = parser.parse_args()

    stub = controller(connect(find_emulator()))
    mapper = TouchMapper(1080, 1920, pb.Rotation.LANDSCAPE)
    rng = np.random.default_rng(0)
    to_produced: list[float] = []
    to_received: list[float] = []
    misses = 0

    with ScreenStream(stub) as stream, TouchInjector(stub) as touch:
        frames = LatestFrames(stream)
        time.sleep(0.5)
        for trial in range(args.trials):
            name = "LR"[trial % 2]  # alternate so the player stays roughly in place
            x, y = BUTTONS[name]
            idle = frames.latest()
            if idle is None:
                raise SystemExit("No frames: is a match running?")
            ref = patch(idle, x, y)

            t0 = time.time_ns()
            touch.press(0, *mapper.to_touch(x, y))
            lit = wait_for(frames, t0, x, y, ref, changed=True)
            time.sleep(0.05)
            t1 = time.time_ns()
            touch.release(0)
            wait_for(frames, t1, x, y, ref, changed=False)  # let the button go dark again

            if lit is None:
                misses += 1
            else:
                to_produced.append((lit.produced_us * 1_000 - t0) / 1e6)
                to_received.append((lit.received_ns - t0) / 1e6)
            time.sleep(float(rng.uniform(0.15, 0.35)))  # decorrelate from the 60 Hz vsync

    def summary(values: list[float]) -> str:
        if not values:
            return "-"
        a = np.asarray(values)
        return " / ".join(f"{np.percentile(a, q):.1f}" for q in (50, 95, 99))

    print(f"trials={args.trials} detected={len(to_received)} misses={misses}")
    print(f"touch -> game frame produced (ms, p50/p95/p99): {summary(to_produced)}")
    print(f"touch -> frame received      (ms, p50/p95/p99): {summary(to_received)}")


if __name__ == "__main__":
    main()
