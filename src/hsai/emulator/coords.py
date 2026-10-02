"""Map upright frame coordinates to the emulator's touch coordinates.

Frames from ``streamScreenshot`` are delivered upright for the device's current pose, while
``sendTouch``/``streamInputEvent`` expect coordinates in the display's natural (portrait)
orientation. Verified on the emulator with Android's pointer-location overlay: in landscape,
frame (x, y) corresponds to touch (natural_width - y, x).
"""

from __future__ import annotations

from dataclasses import dataclass

from hsai.emulator._proto import emulator_controller_pb2 as pb

SkinRotation = pb.Rotation.SkinRotation


@dataclass(frozen=True, slots=True)
class TouchMapper:
    natural_width: int
    """Display width in its natural orientation (e.g. 1080 for a 1080x1920 portrait panel)."""
    natural_height: int
    rotation: SkinRotation

    def __post_init__(self) -> None:
        if self.rotation not in (pb.Rotation.PORTRAIT, pb.Rotation.LANDSCAPE):
            # Reverse orientations follow by symmetry but have not been verified on a device.
            name = pb.Rotation.SkinRotation.Name(self.rotation)
            raise NotImplementedError(f"Unverified rotation: {name}")

    @property
    def frame_size(self) -> tuple[int, int]:
        """(width, height) of upright frames at native resolution."""
        if self.rotation == pb.Rotation.LANDSCAPE:
            return self.natural_height, self.natural_width
        return self.natural_width, self.natural_height

    def to_touch(self, x: float, y: float) -> tuple[int, int]:
        """Native-resolution frame coordinates -> touch coordinates."""
        width, height = self.frame_size
        if not (0 <= x < width and 0 <= y < height):
            raise ValueError(f"({x}, {y}) is outside the {width}x{height} frame")
        if self.rotation == pb.Rotation.LANDSCAPE:
            return round(self.natural_width - 1 - y), round(x)
        return round(x), round(y)

    def to_touch_normalized(self, u: float, v: float) -> tuple[int, int]:
        """Frame coordinates as fractions of width/height in [0, 1) -> touch coordinates."""
        width, height = self.frame_size
        return self.to_touch(u * width, v * height)
