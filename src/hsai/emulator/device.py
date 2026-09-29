"""Device-level state of the emulator (physical orientation)."""

from __future__ import annotations

from typing import Literal

from hsai.emulator._proto import emulator_controller_pb2 as pb
from hsai.emulator._proto.emulator_controller_pb2_grpc import EmulatorControllerStub

Orientation = Literal["portrait", "landscape"]

# Rotation of the virtual device around its z axis, in degrees. 90 is the landscape pose the
# emulator window uses when rotated left once.
_Z_ROTATION: dict[Orientation, float] = {"portrait": 0.0, "landscape": 90.0}


def set_orientation(stub: EmulatorControllerStub, orientation: Orientation) -> None:
    """Rotate the virtual device. Screenshots are delivered upright for this pose."""
    value = pb.ParameterValue(data=[0.0, 0.0, _Z_ROTATION[orientation]])
    stub.setPhysicalModel(pb.PhysicalModelValue(target=pb.PhysicalModelValue.ROTATION, value=value))


def orientation(stub: EmulatorControllerStub) -> Orientation:
    reply = stub.getPhysicalModel(pb.PhysicalModelValue(target=pb.PhysicalModelValue.ROTATION))
    z = reply.value.data[2] % 360 if reply.value.data else 0.0
    return "landscape" if 45 <= z < 135 else "portrait"
