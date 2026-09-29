"""F0 spike: throughput and latency of emulator screen capture over gRPC.

Frames are only delivered when the screen changes, so run this while something animates
(for example, during a match).

    uv run python scripts/spikes/capture_benchmark.py --seconds 10 --width 0 --width 960
"""

from __future__ import annotations

import argparse
import time
from dataclasses import dataclass

import numpy as np

from hsai.emulator import ScreenStream, connect, controller, find_emulator
from hsai.emulator.screen import PixelFormat


@dataclass
class Result:
    label: str
    shape: tuple[int, ...]
    frames: int
    fps: float
    dropped: int
    latency_ms: np.ndarray
    interval_ms: np.ndarray


def run(stub, width: int, pixel_format: PixelFormat, seconds: float) -> Result:  # type: ignore[no-untyped-def]
    latencies: list[float] = []
    arrivals: list[int] = []
    seqs: list[int] = []
    shape: tuple[int, ...] = ()
    with ScreenStream(stub, width=width, pixel_format=pixel_format) as stream:
        deadline = time.monotonic() + seconds
        for frame in stream:
            latencies.append(frame.capture_latency_ms)
            arrivals.append(frame.received_ns)
            seqs.append(frame.seq)
            shape = frame.pixels.shape
            if time.monotonic() >= deadline:
                break
    span_s = (arrivals[-1] - arrivals[0]) / 1e9 if len(arrivals) > 1 else float("nan")
    return Result(
        label=f"width={width or 'native'} {pixel_format}",
        shape=shape,
        frames=len(arrivals),
        fps=(len(arrivals) - 1) / span_s if len(arrivals) > 1 else 0.0,
        dropped=int(np.sum(np.diff(seqs) - 1)) if len(seqs) > 1 else 0,
        latency_ms=np.asarray(latencies),
        interval_ms=np.diff(np.asarray(arrivals)) / 1e6,
    )


def pct(values: np.ndarray, q: float) -> str:
    return f"{np.percentile(values, q):.1f}" if values.size else "-"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seconds", type=float, default=10.0)
    parser.add_argument("--width", type=int, action="append", help="0 = native; repeatable")
    parser.add_argument("--format", choices=["rgb", "rgba"], default="rgb")
    args = parser.parse_args()

    stub = controller(connect(find_emulator()))
    results = [run(stub, w, args.format, args.seconds) for w in (args.width or [0])]

    print(
        "| config | frame | frames | fps | dropped | latency p50/p95/p99 ms | interval p50/p95 ms |"
    )
    print("|---|---|---|---|---|---|---|")
    for r in results:
        print(
            f"| {r.label} | {'x'.join(map(str, r.shape))} | {r.frames} | {r.fps:.1f} "
            f"| {r.dropped} | {pct(r.latency_ms, 50)}/{pct(r.latency_ms, 95)}/"
            f"{pct(r.latency_ms, 99)} | {pct(r.interval_ms, 50)}/{pct(r.interval_ms, 95)} |"
        )


if __name__ == "__main__":
    main()
