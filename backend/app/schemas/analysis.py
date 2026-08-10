"""
Analysis-related Pydantic schemas.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AnalysisStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class UploadSourceRequest(BaseModel):
    """Request schema for uploading source code."""
    c_filename: str = Field(..., description="Original C source filename")
    fortran_filename: str = Field(..., description="Original Fortran source filename")
    project_name: Optional[str] = Field(None, description="Optional project name")


class AnalysisSummary(BaseModel):
    """Summary of a completed analysis."""
    session_id: str
    status: AnalysisStatus
    c_filename: str
    fortran_filename: str
    c_functions_found: int
    fortran_functions_found: int
    gaps_detected: int
    high_severity_gaps: int
    created_at: str
    completed_at: Optional[str] = None
    error: Optional[str] = None


class FunctionIRSchema(BaseModel):
    name: str
    language: str
    parameters: List[str]
    return_type: Optional[str]
    loc: int  # lines of code


class AnalysisResultSchema(BaseModel):
    session_id: str
    status: AnalysisStatus
    c_analysis: Dict[str, Any]
    fortran_analysis: Dict[str, Any]
    ir_summary: Dict[str, Any]
    gaps: List[Dict[str, Any]]
    created_at: str
