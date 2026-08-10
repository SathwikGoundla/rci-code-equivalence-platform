"""TestCase ORM model."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, Text, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TestCase(Base):
    __tablename__ = "test_cases"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("analysis_sessions.id", ondelete="CASCADE"), nullable=False
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    inputs_json: Mapped[str] = mapped_column(Text, nullable=False)  # JSON
    expected_behavior: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")

    # Execution results
    c_exit_code: Mapped[int] = mapped_column(String(8), nullable=True)
    c_stdout: Mapped[str] = mapped_column(Text, nullable=True)
    c_stderr: Mapped[str] = mapped_column(Text, nullable=True)
    c_execution_time_ms: Mapped[float] = mapped_column(Float, nullable=True)

    fortran_exit_code: Mapped[int] = mapped_column(String(8), nullable=True)
    fortran_stdout: Mapped[str] = mapped_column(Text, nullable=True)
    fortran_stderr: Mapped[str] = mapped_column(Text, nullable=True)
    fortran_execution_time_ms: Mapped[float] = mapped_column(Float, nullable=True)

    # Comparison
    comparison_result: Mapped[str] = mapped_column(String(64), nullable=True)
    comparison_detail_json: Mapped[str] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(tz=timezone.utc),
        nullable=False,
    )
    executed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def __repr__(self) -> str:
        return f"<TestCase id={self.id!r} name={self.name!r} status={self.status!r}>"
