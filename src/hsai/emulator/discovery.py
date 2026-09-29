"""Find running Android emulators through the discovery files they write at startup.

Each emulator instance writes ``pid_<pid>.ini`` into a per-user directory. The file holds
``key=value`` lines, including the gRPC port and, when started with ``-grpc-use-token``, the
bearer token that the gRPC endpoint requires.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

DISCOVERY_DIR = Path.home() / "Library" / "Caches" / "TemporaryItems" / "avd" / "running"


class EmulatorNotFoundError(RuntimeError):
    """No running emulator with a gRPC endpoint matched the request."""


@dataclass(frozen=True, slots=True)
class EmulatorEndpoint:
    pid: int
    avd_name: str | None
    grpc_port: int
    grpc_token: str | None

    @property
    def address(self) -> str:
        return f"127.0.0.1:{self.grpc_port}"


def parse_discovery_file(text: str, pid: int) -> EmulatorEndpoint | None:
    """Parse a discovery file; returns None when the instance exposes no gRPC endpoint."""
    fields: dict[str, str] = {}
    for line in text.splitlines():
        key, sep, value = line.partition("=")
        if sep:
            fields[key.strip()] = value.strip()
    if "grpc.port" not in fields:
        return None
    return EmulatorEndpoint(
        pid=pid,
        avd_name=fields.get("avd.name"),
        grpc_port=int(fields["grpc.port"]),
        grpc_token=fields.get("grpc.token") or None,
    )


def _is_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def running_emulators(directory: Path = DISCOVERY_DIR) -> list[EmulatorEndpoint]:
    """All live emulators with a gRPC endpoint. Stale files from crashed instances are skipped."""
    endpoints: list[EmulatorEndpoint] = []
    for path in sorted(directory.glob("pid_*.ini")):
        pid = int(path.stem.removeprefix("pid_"))
        if not _is_alive(pid):
            continue
        endpoint = parse_discovery_file(path.read_text(), pid)
        if endpoint is not None:
            endpoints.append(endpoint)
    return endpoints


def find_emulator(avd_name: str | None = None, directory: Path = DISCOVERY_DIR) -> EmulatorEndpoint:
    """The single running emulator (optionally filtered by AVD name)."""
    candidates = [
        e for e in running_emulators(directory) if avd_name is None or e.avd_name == avd_name
    ]
    if not candidates:
        wanted = f"AVD '{avd_name}'" if avd_name else "any AVD"
        raise EmulatorNotFoundError(
            f"No running emulator with a gRPC endpoint for {wanted} (looked in {directory}). "
            "Start one with scripts/start_emulator.sh."
        )
    if len(candidates) > 1:
        pids = ", ".join(str(e.pid) for e in candidates)
        raise EmulatorNotFoundError(f"Several matching emulators are running (pids {pids}).")
    return candidates[0]
