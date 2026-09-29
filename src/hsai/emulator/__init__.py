"""Capture and input for the Android emulator over its gRPC control API."""

from hsai.emulator.client import connect, controller
from hsai.emulator.discovery import EmulatorEndpoint, EmulatorNotFoundError, find_emulator
from hsai.emulator.screen import Frame, ScreenStream
from hsai.emulator.touch import TouchInjector

__all__ = [
    "EmulatorEndpoint",
    "EmulatorNotFoundError",
    "Frame",
    "ScreenStream",
    "TouchInjector",
    "connect",
    "controller",
    "find_emulator",
]
