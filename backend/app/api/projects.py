"""
Projects API Endpoints

GET  /api/v1/projects/          — List all projects
POST /api/v1/projects/          — Create a project
GET  /api/v1/projects/{id}      — Get project details
DELETE /api/v1/projects/{id}    — Delete a project
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.project import Project

logger = logging.getLogger(__name__)
router = APIRouter()


class CreateProjectRequest(BaseModel):
    name: str
    description: str = ""


@router.get("/projects/", summary="List all projects")
async def list_projects(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).order_by(Project.created_at.desc()))
    projects = result.scalars().all()
    return [
        {
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "created_at": p.created_at.isoformat(),
        }
        for p in projects
    ]


@router.post("/projects/", status_code=201, summary="Create a project")
async def create_project(
    request: CreateProjectRequest, db: AsyncSession = Depends(get_db)
):
    project = Project(
        id=str(uuid.uuid4()),
        name=request.name,
        description=request.description,
    )
    db.add(project)
    await db.flush()
    return {"id": project.id, "name": project.name, "created_at": project.created_at.isoformat()}


@router.get("/projects/{project_id}", summary="Get project details")
async def get_project(project_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")
    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "created_at": project.created_at.isoformat(),
    }


@router.delete("/projects/{project_id}", status_code=204, summary="Delete a project")
async def delete_project(project_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")
    await db.delete(project)
