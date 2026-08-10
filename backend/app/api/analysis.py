"""
Analysis API Endpoints

POST /api/v1/analysis/upload   — Upload C + Fortran source files
GET  /api/v1/analysis/{id}     — Get analysis results
GET  /api/v1/analysis/         — List all analyses
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.analyzers.c.analyzer import analyze_c_source
from app.analyzers.fortran.analyzer import analyze_fortran_source
from app.comparison.engine import compare_programs
from app.config import get_settings
from app.database import get_db
from app.gap_detection.engine import GapDetectionEngine
from app.models.analysis import AnalysisSession
from app.schemas.analysis import AnalysisResultSchema, AnalysisStatus

import json

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()

_gap_engine = GapDetectionEngine()


@router.post("/analysis/upload", response_model=AnalysisResultSchema, summary="Upload and analyze source files")
async def upload_and_analyze(
    c_file: UploadFile = File(..., description="C source file (.c)"),
    fortran_file: UploadFile = File(..., description="Fortran source file (.f90 or .f)"),
    db: AsyncSession = Depends(get_db),
) -> AnalysisResultSchema:
    """
    Upload C and Fortran source files, analyze them, and return the analysis result.
    Source code is NEVER stored in the database — only metadata and analysis results.
    """
    # Validate file sizes
    c_content = await c_file.read()
    f_content = await fortran_file.read()

    if len(c_content) > settings.max_source_file_size:
        raise HTTPException(
            status_code=413,
            detail=f"C file too large. Maximum size: {settings.max_source_file_size} bytes.",
        )
    if len(f_content) > settings.max_source_file_size:
        raise HTTPException(
            status_code=413,
            detail=f"Fortran file too large. Maximum size: {settings.max_source_file_size} bytes.",
        )

    c_source = c_content.decode("utf-8", errors="replace")
    fortran_source = f_content.decode("utf-8", errors="replace")
    session_id = str(uuid.uuid4())

    # Create analysis session record
    session = AnalysisSession(
        id=session_id,
        status="running",
        c_filename=c_file.filename,
        fortran_filename=fortran_file.filename,
        c_file_size=len(c_content),
        fortran_file_size=len(f_content),
    )
    db.add(session)
    await db.flush()

    try:
        # ── Parse ─────────────────────────────────────────────────────────────
        c_ir = analyze_c_source(c_source, filename=c_file.filename or "unknown.c")
        fortran_ir = analyze_fortran_source(
            fortran_source, filename=fortran_file.filename or "unknown.f90"
        )

        # ── Compare ───────────────────────────────────────────────────────────
        comparison = compare_programs(c_ir, fortran_ir)

        # ── Detect Gaps ───────────────────────────────────────────────────────
        gaps = _gap_engine.detect(comparison)
        high_severity = sum(
            1 for g in gaps if g.severity.value in {"HIGH", "CRITICAL"}
        )

        # ── Update session ────────────────────────────────────────────────────
        c_analysis_data = {
            "filename": c_ir.metadata.filename,
            "parser_used": c_ir.metadata.parser_used,
            "total_lines": c_ir.metadata.total_lines,
            "total_loc": c_ir.metadata.total_loc,
            "functions": [
                {
                    "name": f.name,
                    "kind": f.kind,
                    "parameters": [p.name for p in f.parameters],
                    "return_type": f.return_type.value if f.return_type else None,
                    "loc": f.loc,
                    "cyclomatic_complexity": f.cyclomatic_complexity,
                    "has_loops": f.has_loops,
                    "has_conditionals": f.has_conditionals,
                    "has_io": f.has_io,
                    "calls": f.calls,
                }
                for f in c_ir.functions
            ],
            "constants": [{"name": c.name, "value": c.initial_value} for c in c_ir.constants],
            "includes": c_ir.includes,
            "warnings": c_ir.metadata.parse_warnings,
        }

        fortran_analysis_data = {
            "filename": fortran_ir.metadata.filename,
            "parser_used": fortran_ir.metadata.parser_used,
            "total_lines": fortran_ir.metadata.total_lines,
            "total_loc": fortran_ir.metadata.total_loc,
            "functions": [
                {
                    "name": f.name,
                    "kind": f.kind,
                    "parameters": [p.name for p in f.parameters],
                    "return_type": f.return_type.value if f.return_type else None,
                    "loc": f.loc,
                    "cyclomatic_complexity": f.cyclomatic_complexity,
                    "has_loops": f.has_loops,
                    "has_conditionals": f.has_conditionals,
                    "has_io": f.has_io,
                    "has_implicit_none": f.has_implicit_none,
                }
                for f in fortran_ir.functions
            ],
            "constants": [{"name": c.name, "value": c.initial_value} for c in fortran_ir.constants],
            "modules": fortran_ir.modules,
            "warnings": fortran_ir.metadata.parse_warnings,
        }

        ir_summary = {
            "structural_score": comparison.structural_score,
            "matched_functions": comparison.matched_functions,
            "c_only_functions": comparison.c_only_functions,
            "fortran_only_functions": comparison.fortran_only_functions,
            "notes": comparison.notes,
        }

        session.status = "completed"
        session.c_functions_found = c_ir.function_count
        session.fortran_functions_found = fortran_ir.function_count
        session.gaps_detected = len(gaps)
        session.high_severity_gaps = high_severity
        session.c_analysis_json = json.dumps(c_analysis_data)
        session.fortran_analysis_json = json.dumps(fortran_analysis_data)
        session.ir_json = json.dumps(ir_summary)
        session.completed_at = datetime.now(tz=timezone.utc)

        return AnalysisResultSchema(
            session_id=session_id,
            status=AnalysisStatus.COMPLETED,
            c_analysis=c_analysis_data,
            fortran_analysis=fortran_analysis_data,
            ir_summary=ir_summary,
            gaps=[g.to_dict() for g in gaps],
            created_at=session.created_at.isoformat(),
        )

    except Exception as exc:
        logger.error("Analysis failed for session %s: %s", session_id, exc, exc_info=True)
        session.status = "failed"
        session.error_message = str(exc)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Analysis failed",
                "detail": str(exc),
                "session_id": session_id,
            },
        )


@router.get("/analysis/", summary="List analysis sessions")
async def list_analyses(db: AsyncSession = Depends(get_db)):
    """Return a list of all analysis sessions (metadata only, no source code)."""
    from sqlalchemy import select
    result = await db.execute(
        select(AnalysisSession).order_by(AnalysisSession.created_at.desc()).limit(50)
    )
    sessions = result.scalars().all()
    return [
        {
            "session_id": s.id,
            "status": s.status,
            "c_filename": s.c_filename,
            "fortran_filename": s.fortran_filename,
            "c_functions_found": s.c_functions_found,
            "fortran_functions_found": s.fortran_functions_found,
            "gaps_detected": s.gaps_detected,
            "high_severity_gaps": s.high_severity_gaps,
            "created_at": s.created_at.isoformat() if s.created_at else None,
            "completed_at": s.completed_at.isoformat() if s.completed_at else None,
        }
        for s in sessions
    ]


@router.get("/analysis/{session_id}", summary="Get analysis result by session ID")
async def get_analysis(session_id: str, db: AsyncSession = Depends(get_db)):
    """Return the full analysis result for a session."""
    from sqlalchemy import select
    result = await db.execute(
        select(AnalysisSession).where(AnalysisSession.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail=f"Analysis session '{session_id}' not found.")

    c_analysis = json.loads(session.c_analysis_json) if session.c_analysis_json else {}
    fortran_analysis = json.loads(session.fortran_analysis_json) if session.fortran_analysis_json else {}
    ir_summary = json.loads(session.ir_json) if session.ir_json else {}

    return {
        "session_id": session.id,
        "status": session.status,
        "c_filename": session.c_filename,
        "fortran_filename": session.fortran_filename,
        "c_analysis": c_analysis,
        "fortran_analysis": fortran_analysis,
        "ir_summary": ir_summary,
        "gaps_detected": session.gaps_detected,
        "high_severity_gaps": session.high_severity_gaps,
        "created_at": session.created_at.isoformat() if session.created_at else None,
        "completed_at": session.completed_at.isoformat() if session.completed_at else None,
        "error": session.error_message,
    }
