import uuid
from datetime import datetime

from sqlalchemy import String, Integer, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ModelEndpoint(Base):
    __tablename__ = "model_endpoints"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False)
    model_name: Mapped[str] = mapped_column(String, nullable=False)  # e.g. gpt-4, llama2
    provider: Mapped[str] = mapped_column(String, nullable=False)
    base_url: Mapped[str] = mapped_column(String, nullable=False)
    api_key: Mapped[str] = mapped_column(String, nullable=False)
    context_window: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cost_per_1k_input: Mapped[float | None] = mapped_column(Float, nullable=True)
    cost_per_1k_output: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_judge: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    creator: Mapped["User"] = relationship("User")  # type: ignore[name-defined]
