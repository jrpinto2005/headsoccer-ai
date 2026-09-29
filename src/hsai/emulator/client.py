"""gRPC channel to the emulator's ``EmulatorController`` service."""

from __future__ import annotations

from typing import NamedTuple

import grpc

from hsai.emulator._proto.emulator_controller_pb2_grpc import EmulatorControllerStub
from hsai.emulator.discovery import EmulatorEndpoint

# A full-resolution RGBA frame is ~8 MB, above gRPC's 4 MB default.
_MAX_MESSAGE_BYTES = 64 * 1024 * 1024


class _CallDetails(NamedTuple):
    method: str
    timeout: float | None
    metadata: tuple[tuple[str, str | bytes], ...] | None
    credentials: grpc.CallCredentials | None
    wait_for_ready: bool | None
    compression: grpc.Compression | None


class _ClientCallDetails(_CallDetails, grpc.ClientCallDetails):
    pass


class _BearerTokenInterceptor(
    grpc.UnaryUnaryClientInterceptor,
    grpc.UnaryStreamClientInterceptor,
    grpc.StreamUnaryClientInterceptor,
    grpc.StreamStreamClientInterceptor,
):
    """Adds the emulator's per-session token to every call."""

    def __init__(self, token: str) -> None:
        self._header = ("authorization", f"Bearer {token}")

    def _with_token(self, details: grpc.ClientCallDetails) -> grpc.ClientCallDetails:
        metadata = (*(details.metadata or ()), self._header)
        return _ClientCallDetails(
            details.method,
            details.timeout,
            metadata,
            details.credentials,
            getattr(details, "wait_for_ready", None),
            getattr(details, "compression", None),
        )

    def intercept_unary_unary(self, continuation, client_call_details, request):  # type: ignore[no-untyped-def]
        return continuation(self._with_token(client_call_details), request)

    def intercept_unary_stream(self, continuation, client_call_details, request):  # type: ignore[no-untyped-def]
        return continuation(self._with_token(client_call_details), request)

    def intercept_stream_unary(self, continuation, client_call_details, request_iterator):  # type: ignore[no-untyped-def]
        return continuation(self._with_token(client_call_details), request_iterator)

    def intercept_stream_stream(self, continuation, client_call_details, request_iterator):  # type: ignore[no-untyped-def]
        return continuation(self._with_token(client_call_details), request_iterator)


def connect(endpoint: EmulatorEndpoint) -> grpc.Channel:
    options = [
        ("grpc.max_receive_message_length", _MAX_MESSAGE_BYTES),
        ("grpc.max_send_message_length", _MAX_MESSAGE_BYTES),
    ]
    channel = grpc.insecure_channel(endpoint.address, options=options)
    if endpoint.grpc_token:
        channel = grpc.intercept_channel(channel, _BearerTokenInterceptor(endpoint.grpc_token))
    return channel


def controller(channel: grpc.Channel) -> EmulatorControllerStub:
    return EmulatorControllerStub(channel)
