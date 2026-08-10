"""
System Information Service

Collects OS, Python, disk, and platform information for the diagnostics page.
All information is gathered locally — no external calls.
"""

from __future__ import annotations

import platform
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import psutil


@dataclass
class DiskInfo:
    total_gb: float
    used_gb: float
    free_gb: float
    percent_used: float


@dataclass
class SystemInfo:
    os_name: str
    os_version: str
    os_platform: str
    python_version: str
    python_executable: str
    architecture: str
    cpu_count: int
    total_memory_gb: float
    available_memory_gb: float
    disk: DiskInfo
    node_version: Optional[str]
    is_offline: bool = True


def _get_node_version() -> Optional[str]:
    """Try to detect the installed Node.js version."""
    node_path = shutil.which("node")
    if not node_path:
        return None
    try:
        import subprocess
        result = subprocess.run(
            [node_path, "--version"],
            capture_output=True, text=True, timeout=5
        )
        return result.stdout.strip()
    except Exception:
        return None


def get_system_info() -> SystemInfo:
    """Collect comprehensive system information for the diagnostics page."""

    # Disk info for the application's working directory
    cwd = Path.cwd()
    disk = shutil.disk_usage(str(cwd))

    # Memory
    memory = psutil.virtual_memory()

    return SystemInfo(
        os_name=platform.system(),
        os_version=platform.version(),
        os_platform=platform.platform(),
        python_version=sys.version,
        python_executable=sys.executable,
        architecture=platform.machine(),
        cpu_count=psutil.cpu_count(logical=True) or 0,
        total_memory_gb=round(memory.total / (1024 ** 3), 2),
        available_memory_gb=round(memory.available / (1024 ** 3), 2),
        disk=DiskInfo(
            total_gb=round(disk.total / (1024 ** 3), 2),
            used_gb=round(disk.used / (1024 ** 3), 2),
            free_gb=round(disk.free / (1024 ** 3), 2),
            percent_used=round((disk.used / disk.total) * 100, 1),
        ),
        node_version=_get_node_version(),
        is_offline=True,
    )
