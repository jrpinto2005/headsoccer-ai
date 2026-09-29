import os
from pathlib import Path

import pytest

from hsai.emulator.discovery import (
    EmulatorNotFoundError,
    find_emulator,
    parse_discovery_file,
    running_emulators,
)

DISCOVERY = """\
port.serial=5554
port.adb=5555
avd.name=hsai
grpc.port=8554
grpc.token=s3cr3t
"""


def test_parse_reads_grpc_fields() -> None:
    endpoint = parse_discovery_file(DISCOVERY, pid=42)
    assert endpoint is not None
    assert endpoint.avd_name == "hsai"
    assert endpoint.address == "127.0.0.1:8554"
    assert endpoint.grpc_token == "s3cr3t"


def test_parse_without_grpc_returns_none() -> None:
    assert parse_discovery_file("avd.name=hsai\nport.serial=5554\n", pid=42) is None


def test_parse_without_token() -> None:
    endpoint = parse_discovery_file("grpc.port=8554\n", pid=42)
    assert endpoint is not None
    assert endpoint.grpc_token is None


def test_stale_files_are_ignored(tmp_path: Path) -> None:
    live = os.getpid()
    (tmp_path / f"pid_{live}.ini").write_text(DISCOVERY)
    (tmp_path / "pid_999999.ini").write_text(DISCOVERY.replace("8554", "8556"))
    assert [e.pid for e in running_emulators(tmp_path)] == [live]


def test_find_filters_by_avd_name(tmp_path: Path) -> None:
    (tmp_path / f"pid_{os.getpid()}.ini").write_text(DISCOVERY)
    assert find_emulator("hsai", tmp_path).grpc_port == 8554
    with pytest.raises(EmulatorNotFoundError):
        find_emulator("other", tmp_path)
