"""Launcher that starts the MCP server and public API together."""

from __future__ import annotations

import signal
import subprocess
import sys
import time
from collections.abc import Sequence


def _spawn(module_name: str) -> subprocess.Popen[str]:
    return subprocess.Popen(
        [sys.executable, "-m", module_name],
        stdout=None,
        stderr=None,
    )


def _terminate(processes: Sequence[subprocess.Popen[str]]) -> None:
    for process in processes:
        if process.poll() is None:
            process.terminate()

    for process in processes:
        if process.poll() is None:
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()


def main() -> None:
    """Run both services in a single command."""

    processes = [
        _spawn("philter_mcp_server.mcp_main"),
        _spawn("philter_mcp_server.__main__"),
    ]

    def shutdown(_signum: int | None = None, _frame: object | None = None) -> None:
        _terminate(processes)
        raise SystemExit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    try:
        while True:
            for process in processes:
                exit_code = process.poll()
                if exit_code is not None:
                    if exit_code != 0:
                        _terminate(processes)
                        raise SystemExit(exit_code)
                    other_processes = [other for other in processes if other is not process]
                    _terminate(other_processes)
                    raise SystemExit(0)

            time.sleep(0.5)
    except KeyboardInterrupt:
        shutdown()
