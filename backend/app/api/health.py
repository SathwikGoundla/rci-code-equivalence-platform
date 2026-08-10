"""
Health and System-Status Endpoints

GET /api/v1/health          — Simple liveness check
GET /api/v1/status          — Detailed application status
GET /api/v1/system-info     — OS, compilers, Python, disk, etc.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter

from app.config import get_settings
from app.schemas.system import (
    HealthResponse,
    SystemStatusResponse,
    SystemInfoResponse,
    CompilerInfoSchema,
)
from app.services.compiler_detection import detect_all_compilers, CompilerStatus
from app.services.system_info import get_system_info

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()

# Track startup time for uptime calculation
_startup_time = datetime.now(tz=timezone.utc)


@router.get("/health", response_model=HealthResponse, summary="Liveness check")
async def health() -> HealthResponse:
    """
    Returns 200 OK when the application is running.
    No database query — pure liveness probe.
    """
    return HealthResponse(
        status="healthy",
        offline=True,
        version=settings.app_version,
        timestamp=datetime.now(tz=timezone.utc).isoformat(),
    )


@router.get("/status", response_model=SystemStatusResponse, summary="Application status")
async def status() -> SystemStatusResponse:
    """
    Returns compiler status, application version, and uptime.
    """
    compilers = detect_all_compilers()
    uptime_seconds = (datetime.now(tz=timezone.utc) - _startup_time).total_seconds()

    return SystemStatusResponse(
        status="operational",
        offline=True,
        version=settings.app_version,
        environment=settings.app_env,
        uptime_seconds=round(uptime_seconds, 1),
        has_c_compiler=compilers.has_c_compiler,
        has_fortran_compiler=compilers.has_fortran_compiler,
        local_ai_enabled=settings.local_ai_enabled,
        timestamp=datetime.now(tz=timezone.utc).isoformat(),
    )


@router.get("/system-info", response_model=SystemInfoResponse, summary="Full system diagnostics")
async def system_info() -> SystemInfoResponse:
    """
    Returns comprehensive system information for the diagnostics dashboard.
    Includes OS, Python version, compiler details, memory, and disk info.
    """
    sys_info = get_system_info()
    compilers = detect_all_compilers()

    c_compiler_infos = [
        CompilerInfoSchema(
            name=c.name,
            language=c.language,
            status=c.status.value,
            path=c.path,
            version=c.version,
            version_string=c.version_string,
            error=c.error,
        )
        for c in compilers.c_compilers
    ]

    fortran_compiler_infos = [
        CompilerInfoSchema(
            name=c.name,
            language=c.language,
            status=c.status.value,
            path=c.path,
            version=c.version,
            version_string=c.version_string,
            error=c.error,
        )
        for c in compilers.fortran_compilers
    ]

    return SystemInfoResponse(
        os_name=sys_info.os_name,
        os_version=sys_info.os_version,
        os_platform=sys_info.os_platform,
        python_version=sys_info.python_version,
        python_executable=sys_info.python_executable,
        architecture=sys_info.architecture,
        cpu_count=sys_info.cpu_count,
        total_memory_gb=sys_info.total_memory_gb,
        available_memory_gb=sys_info.available_memory_gb,
        disk_total_gb=sys_info.disk.total_gb,
        disk_used_gb=sys_info.disk.used_gb,
        disk_free_gb=sys_info.disk.free_gb,
        disk_percent_used=sys_info.disk.percent_used,
        node_version=sys_info.node_version,
        c_compilers=c_compiler_infos,
        fortran_compilers=fortran_compiler_infos,
        app_version=settings.app_version,
        offline=True,
        local_ai_enabled=settings.local_ai_enabled,
        local_ai_provider=settings.ollama_model if settings.local_ai_enabled else None,
        timestamp=datetime.now(tz=timezone.utc).isoformat(),
    )
