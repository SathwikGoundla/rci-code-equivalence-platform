import pytest
import os
import json


@pytest.mark.asyncio
async def test_get_settings_returns_defaults(async_client):
    # Ensure config.json doesn't exist during test
    if os.path.exists("config.json"):
        os.remove("config.json")
        
    response = await async_client.get("/api/v1/settings/")
    assert response.status_code == 200
    data = response.json()
    assert "execution_timeout" in data
    assert "c_compiler_path" in data
    assert "fortran_compiler_path" in data
    assert data["atol"] == 1e-6
    assert data["rtol"] == 1e-9


@pytest.mark.asyncio
async def test_update_settings_persists(async_client):
    if os.path.exists("config.json"):
        os.remove("config.json")

    payload = {
        "execution_timeout": 45,
        "c_compiler_path": "/test/path/gcc",
        "fortran_compiler_path": "/test/path/gfortran",
        "atol": 1e-5,
        "rtol": 1e-8
    }
    response = await async_client.post("/api/v1/settings/", json=payload)
    assert response.status_code == 200
    
    # Retrieve settings and verify they match overrides
    get_res = await async_client.get("/api/v1/settings/")
    assert get_res.status_code == 200
    data = get_res.json()
    assert data["execution_timeout"] == 45
    assert data["c_compiler_path"] == "/test/path/gcc"
    assert data["fortran_compiler_path"] == "/test/path/gfortran"
    assert data["atol"] == 1e-5
    assert data["rtol"] == 1e-8

    # Clean up
    if os.path.exists("config.json"):
        os.remove("config.json")
