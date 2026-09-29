"""Screen capture through the emulator's ``streamScreenshot`` RPC."""

from __future__ import annotations

import time
from collections.abc import Iterator
from dataclasses import dataclass
from types import TracebackType
from typing import Literal, Self

import grpc
import numpy as np
import numpy.typing as npt

from hsai.emulator._proto import emulator_controller_pb2 as pb
from hsai.emulator._proto.emulator_controller_pb2_grpc import EmulatorControllerStub

PixelFormat = Literal["rgb", "rgba"]

_FORMATS: dict[PixelFormat, tuple[pb.ImageFormat.ImgFormat, int]] = {
    "rgb": (pb.ImageFormat.RGB888, 3),
    "rgba": (pb.ImageFormat.RGBA8888, 4),
}


@dataclass(frozen=True, slots=True)
class Frame:
    pixels: npt.NDArray[np.uint8]
    """(height, width, channels), top row first. Read-only view over the received buffer."""
    seq: int
    """Emulator sequence number; gaps mean frames were skipped."""
    produced_us: int
    """Emulator's estimate of when the guest produced the frame (Unix epoch, µs)."""
    received_ns: int
    """Host wall clock when the frame was fully received (Unix epoch, ns)."""

    @property
    def capture_latency_ms(self) -> float:
        return (self.received_ns / 1_000 - self.produced_us) / 1_000


class ScreenStream:
    """Frames from ``streamScreenshot``, delivered as soon as the guest posts them.

    ``width``/``height`` request emulator-side downscaling (aspect ratio is kept); 0 means the
    native display size.
    """

    def __init__(
        self,
        stub: EmulatorControllerStub,
        *,
        width: int = 0,
        height: int = 0,
        pixel_format: PixelFormat = "rgb",
    ) -> None:
        image_format, self._channels = _FORMATS[pixel_format]
        self._request = pb.ImageFormat(format=image_format, width=width, height=height)
        self._stub = stub
        self._call: grpc.Future | None = None

    def __iter__(self) -> Iterator[Frame]:
        call = self._stub.streamScreenshot(self._request)
        self._call = call
        try:
            for image in call:
                received_ns = time.time_ns()
                width, height = image.format.width, image.format.height
                if width == 0 or height == 0:  # display inactive
                    continue
                pixels = np.frombuffer(image.image, dtype=np.uint8).reshape(
                    height, width, self._channels
                )
                yield Frame(pixels, image.seq, image.timestampUs, received_ns)
        except grpc.RpcError as error:
            if error.code() != grpc.StatusCode.CANCELLED:  # type: ignore[attr-defined]
                raise

    def close(self) -> None:
        if self._call is not None:
            self._call.cancel()

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()
