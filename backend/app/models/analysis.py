"""Analysis session ORM model."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, Text, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AnalysisSession(Base):
    __tablename__ = "analysis_sessions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="pending"
    )

    # Source files metadata (NOT content — content stays in memory or temp files)
    c_filename: Mapped[str] = mapped_column(String(512), nullable=True)
    fortran_filename: Mapped[str] = mapped_column(String(512), nullable=True)
    c_file_size: Mapped[int] = mapped_column(Integer, nullable=True)
    fortran_file_size: Mapped[int] = mapped_column(Integer, nullable=True)

    # Analysis results (stored as JSON strings)
    c_analysis_json: Mapped[str] = mapped_column(Text, nullable=True)
    fortran_analysis_json: Mapped[str] = mapped_column(Text, nullable=True)
    ir_json: Mapped[str] = mapped_column(Text, nullable=True)

    # Counts
    c_functions_found: Mapped[int] = mapped_column(Integer, nullable=True, default=0)
    fortran_functions_found: Mapped[int] = mapped_column(Integer, nullable=True, default=0)
    gaps_detected: Mapped[int] = mapped_column(Integer, nullable=True, default=0)
    high_severity_gaps: Mapped[int] = mapped_column(Integer, nullable=True, default=0)

    error_message: Mapped[str] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(tz=timezone.utc),
        nullable=False,
    )
    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def __repr__(self) -> str:
        return f"<AnalysisSession id={self.id!r} status={self.status!r}>"
