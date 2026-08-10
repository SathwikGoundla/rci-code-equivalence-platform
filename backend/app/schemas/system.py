"""
System-related Pydantic schemas for API responses.
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    offline: bool
    version: str
    timestamp: str


class SystemStatusResponse(BaseModel):
    status: str
    offline: bool
    version: str
    environment: str
    uptime_seconds: float
    has_c_compiler: bool
    has_fortran_compiler: bool
    local_ai_enabled: bool
    timestamp: str


class CompilerInfoSchema(BaseModel):
    name: str
    language: str
    status: str  # "detected" | "not_found" | "error"
    path: Optional[str] = None
    version: Optional[str] = None
    version_string: Optional[str] = None
    error: Optional[str] = None


class SystemInfoResponse(BaseModel):
    # OS
    os_name: str
    os_version: str
    os_platform: str

    # Python
    python_version: str
    python_executable: str
    architecture: str

    # Hardware
    cpu_count: int
    total_memory_gb: float
    available_memory_gb: float

    # Disk
    disk_total_gb: float
    disk_used_gb: float
    disk_free_gb: float
    disk_percent_used: float

    # Runtime
    node_version: Optional[str] = None

    # Compilers
    c_compilers: List[CompilerInfoSchema]
    fortran_compilers: List[CompilerInfoSchema]

    # Application
    app_version: str
    offline: bool
    local_ai_enabled: bool
    local_ai_provider: Optional[str] = None
    timestamp: str
