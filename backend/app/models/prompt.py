import uuid
import re
from datetime import datetime
from typing import List

from sqlalchemy import String, Text, DateTime, ForeignKey, Table, Column, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

prompt_tag_association = Table(
    "prompt_tag_associations",
    Base.metadata,
    Column("prompt_id", UUID(as_uuid=True), ForeignKey("prompts.id"), primary_key=True),
    Column("tag_id", UUID(as_uuid=True), ForeignKey("prompt_tags.id"), primary_key=True),
)


class PromptTag(Base):
    __tablename__ = "prompt_tags"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    prompts: Mapped[List["Prompt"]] = relationship(
        "Prompt", secondary=prompt_tag_association, back_populates="tags"
    )


class Prompt(Base):
    __tablename__ = "prompts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner: Mapped["User"] = relationship("User")  # type: ignore[name-defined]
    tags: Mapped[List[PromptTag]] = relationship(
        PromptTag, secondary=prompt_tag_association, back_populates="prompts"
    )
    versions: Mapped[List["PromptVersion"]] = relationship(
        "PromptVersion",
        back_populates="prompt",
        cascade="all, delete-orphan",
        order_by="desc(PromptVersion.created_at)",
    )


class PromptVersion(Base):
    __tablename__ = "prompt_versions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prompt_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("prompts.id"), nullable=False)
    version_hash: Mapped[str] = mapped_column(String(7), nullable=False, index=True)
    commit_message: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    variables: Mapped[List[str]] = mapped_column(JSON, default=list)
    tag: Mapped[str | None] = mapped_column(String, nullable=True)  # dev, staging, production
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    prompt: Mapped[Prompt] = relationship(Prompt, back_populates="versions")
    creator: Mapped["User"] = relationship("User")  # type: ignore[name-defined]
