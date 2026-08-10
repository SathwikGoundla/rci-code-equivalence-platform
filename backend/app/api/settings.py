"""
Settings API Endpoints

GET  /api/v1/settings/   — Get current system configuration
POST /api/v1/settings/   — Save settings overrides (to config.json)
"""

from __future__ import annotations

import json
import logging
import os
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()

CONFIG_FILE_PATH = "config.json"


class SettingsUpdateRequest(BaseModel):
    execution_timeout: Optional[int] = Field(None, ge=1, le=300)
    c_compiler_path: Optional[str] = None
    fortran_compiler_path: Optional[str] = None
    atol: Optional[float] = Field(None, ge=0.0)
    rtol: Optional[float] = Field(None, ge=0.0)


def load_config_overrides() -> dict:
    """Load configuration overrides from config.json if it exists."""
    if os.path.exists(CONFIG_FILE_PATH):
        try:
            with open(CONFIG_FILE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error("Failed to load config.json: %s", e)
    return {}


def save_config_overrides(overrides: dict) -> None:
    """Save configuration overrides to config.json."""
    try:
        with open(CONFIG_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(overrides, f, indent=2)
    except Exception as e:
        logger.error("Failed to save config.json: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to save settings: {e}")


@router.get("/settings/", summary="Get current settings")
async def get_system_settings():
    settings = get_settings()
    overrides = load_config_overrides()

    # Get tolerances (default to typical values if not set)
    atol = overrides.get("atol", 1e-6)
    rtol = overrides.get("rtol", 1e-9)

    return {
        "execution_timeout": overrides.get("execution_timeout", settings.execution_timeout),
        "c_compiler_path": overrides.get("c_compiler_path", settings.c_compiler_path),
        "fortran_compiler_path": overrides.get("fortran_compiler_path", settings.fortran_compiler_path),
        "atol": atol,
        "rtol": rtol,
        "max_source_file_size": settings.max_source_file_size,
        "offline": True,
    }


@router.post("/settings/", summary="Update system settings")
async def update_system_settings(req: SettingsUpdateRequest):
    overrides = load_config_overrides()

    if req.execution_timeout is not None:
        overrides["execution_timeout"] = req.execution_timeout
    if req.c_compiler_path is not None:
        overrides["c_compiler_path"] = req.c_compiler_path.strip()
    if req.fortran_compiler_path is not None:
        overrides["fortran_compiler_path"] = req.fortran_compiler_path.strip()
    if req.atol is not None:
        overrides["atol"] = req.atol
    if req.rtol is not None:
        overrides["rtol"] = req.rtol

    save_config_overrides(overrides)

    # Dynamically update the cached singleton values if they exist
    settings = get_settings()
    if req.execution_timeout is not None:
        settings.execution_timeout = req.execution_timeout
    if req.c_compiler_path is not None:
        settings.c_compiler_path = req.c_compiler_path.strip()
    if req.fortran_compiler_path is not None:
        settings.fortran_compiler_path = req.fortran_compiler_path.strip()

    return {"status": "success", "message": "Settings updated successfully"}
