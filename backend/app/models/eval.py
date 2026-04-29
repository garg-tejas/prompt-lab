import uuid
from datetime import datetime
from typing import List

from sqlalchemy import String, Text, DateTime, ForeignKey, Float, JSON, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class EvalRun(Base):
    __tablename__ = "eval_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False)
    prompt_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("prompts.id"), nullable=False)
    prompt_version_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("prompt_versions.id"), nullable=False)
    dataset_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("datasets.id"), nullable=False)
    model_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("model_endpoints.id"), nullable=False)
    judge_model_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("model_endpoints.id"), nullable=False)
    status: Mapped[str] = mapped_column(String, default="pending")  # pending, running, completed, failed
    config: Mapped[dict] = mapped_column(JSON, default=dict)
    results_summary: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    results: Mapped[List["EvalResult"]] = relationship(
        "EvalResult", back_populates="eval_run", cascade="all, delete-orphan"
    )


class EvalResult(Base):
    __tablename__ = "eval_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    eval_run_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("eval_runs.id"), nullable=False)
    dataset_row_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("dataset_rows.id"), nullable=False)
    output: Mapped[str] = mapped_column(Text, nullable=False)
    latency_ms: Mapped[float] = mapped_column(Float, nullable=False)
    input_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    output_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    estimated_cost: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    eval_run: Mapped[EvalRun] = relationship(EvalRun, back_populates="results")
    scores: Mapped[List["MetricScore"]] = relationship(
        "MetricScore", back_populates="eval_result", cascade="all, delete-orphan"
    )


class MetricScore(Base):
    __tablename__ = "metric_scores"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    eval_result_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("eval_results.id"), nullable=False)
    metric_name: Mapped[str] = mapped_column(String, nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    judge_model_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("model_endpoints.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    eval_result: Mapped[EvalResult] = relationship(EvalResult, back_populates="scores")
