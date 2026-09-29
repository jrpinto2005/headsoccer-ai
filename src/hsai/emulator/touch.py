"""Multitouch injection through one long-lived ``streamInputEvent`` call.

Keeping a single client stream open avoids per-event RPC setup. Coordinates are in the
emulator's touch space (the display in its natural orientation, in physical pixels).
"""

from __future__ import annotations

import queue
from collections.abc import Iterator
from types import TracebackType
from typing import Self

from hsai.emulator._proto import emulator_controller_pb2 as pb
from hsai.emulator._proto.emulator_controller_pb2_grpc import EmulatorControllerStub

_TOUCHING = 1  # any non-zero pressure means "in contact"; 0 lifts the finger


class TouchInjector:
    """Press, move and release up to 10 independent fingers, each identified by an int."""

    def __init__(self, stub: EmulatorControllerStub) -> None:
        self._events: queue.SimpleQueue[pb.InputEvent | None] = queue.SimpleQueue()
        self._fingers_down: dict[int, tuple[int, int]] = {}
        self._call = stub.streamInputEvent.future(self._drain())

    def _drain(self) -> Iterator[pb.InputEvent]:
        while (event := self._events.get()) is not None:
            yield event

    def _send(self, touches: list[pb.Touch]) -> None:
        self._events.put(pb.InputEvent(touch_event=pb.TouchEvent(touches=touches)))

    def press(self, finger: int, x: int, y: int) -> None:
        """Put a finger down at (x, y), or move it there if it is already down."""
        self._send([pb.Touch(x=x, y=y, identifier=finger, pressure=_TOUCHING)])
        self._fingers_down[finger] = (x, y)

    def release(self, finger: int) -> None:
        position = self._fingers_down.pop(finger, None)
        if position is not None:
            x, y = position
            self._send([pb.Touch(x=x, y=y, identifier=finger, pressure=0)])

    def release_all(self) -> None:
        for finger in list(self._fingers_down):
            self.release(finger)

    @property
    def fingers_down(self) -> frozenset[int]:
        return frozenset(self._fingers_down)

    def close(self, timeout_s: float = 2.0) -> None:
        self.release_all()
        self._events.put(None)
        self._call.result(timeout=timeout_s)

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()
