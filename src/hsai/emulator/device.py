"""Device-level state of the emulator (physical orientation)."""

from __future__ import annotations

import time
from typing import Literal

from hsai.emulator._proto import emulator_controller_pb2 as pb
from hsai.emulator._proto.emulator_controller_pb2_grpc import EmulatorControllerStub

Orientation = Literal["portrait", "landscape"]

# Rotation of the virtual device around its z axis, in degrees. 90 is the landscape pose the
# emulator window uses when rotated left once.
_Z_ROTATION: dict[Orientation, float] = {"portrait": 0.0, "landscape": 90.0}


def _z_rotation(stub: EmulatorControllerStub) -> float:
    reply = stub.getPhysicalModel(pb.PhysicalModelValue(target=pb.PhysicalModelValue.ROTATION))
    return reply.value.data[2] % 360 if reply.value.data else 0.0


def set_orientation(
    stub: EmulatorControllerStub, orientation: Orientation, timeout_s: float = 3.0
) -> None:
    """Rotate the virtual device and wait until the pose settles.

    The emulator interpolates physical-model changes, so the new pose is not visible
    immediately after the call. Screenshots are delivered upright for the final pose.
    """
    target = _Z_ROTATION[orientation]
    value = pb.ParameterValue(data=[0.0, 0.0, target])
    stub.setPhysicalModel(pb.PhysicalModelValue(target=pb.PhysicalModelValue.ROTATION, value=value))
    deadline = time.monotonic() + timeout_s
    while abs(_z_rotation(stub) - target) > 0.5:
        if time.monotonic() > deadline:
            raise TimeoutError(f"Device did not reach {orientation} within {timeout_s} s")
        time.sleep(0.05)


def orientation(stub: EmulatorControllerStub) -> Orientation:
    z = _z_rotation(stub)
    return "landscape" if 45 <= z < 135 else "portrait"
