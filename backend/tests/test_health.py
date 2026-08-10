"""
Tests for health and system-info endpoints.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_returns_200(async_client: AsyncClient):
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_health_response_structure(async_client: AsyncClient):
    response = await async_client.get("/api/v1/health")
    data = response.json()
    assert data["status"] == "healthy"
    assert data["offline"] is True
    assert "version" in data
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_status_endpoint(async_client: AsyncClient):
    response = await async_client.get("/api/v1/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "operational"
    assert data["offline"] is True
    assert "uptime_seconds" in data
    assert isinstance(data["has_c_compiler"], bool)
    assert isinstance(data["has_fortran_compiler"], bool)


@pytest.mark.asyncio
async def test_system_info_endpoint(async_client: AsyncClient):
    response = await async_client.get("/api/v1/system-info")
    assert response.status_code == 200
    data = response.json()
    assert "os_name" in data
    assert "python_version" in data
    assert "c_compilers" in data
    assert "fortran_compilers" in data
    assert isinstance(data["c_compilers"], list)
    assert isinstance(data["fortran_compilers"], list)
    assert data["offline"] is True


@pytest.mark.asyncio
async def test_system_info_has_disk_info(async_client: AsyncClient):
    response = await async_client.get("/api/v1/system-info")
    data = response.json()
    assert "disk_total_gb" in data
    assert "disk_free_gb" in data
    assert data["disk_total_gb"] > 0
    assert data["disk_free_gb"] >= 0


@pytest.mark.asyncio
async def test_process_time_header_present(async_client: AsyncClient):
    response = await async_client.get("/api/v1/health")
    assert "x-process-time" in response.headers
