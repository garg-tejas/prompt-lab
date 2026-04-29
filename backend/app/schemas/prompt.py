from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class PromptTagBase(BaseModel):
    name: str


class PromptTagResponse(PromptTagBase):
    id: UUID
    model_config = ConfigDict(from_attributes=True)


class PromptVersionBase(BaseModel):
    version_hash: str
    commit_message: str
    content: str
    variables: List[str]
    tag: Optional[str] = None


class PromptVersionCreate(BaseModel):
    content: str
    commit_message: str


class PromptVersionResponse(PromptVersionBase):
    id: UUID
    prompt_id: UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class PromptBase(BaseModel):
    name: str
    description: Optional[str] = None


class PromptCreate(PromptBase):
    content: str
    commit_message: str
    tags: List[str] = []


class PromptUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None


class PromptListResponse(PromptBase):
    id: UUID
    owner_id: UUID
    tags: List[PromptTagResponse]
    created_at: datetime
    updated_at: datetime
    version_count: int
    latest_version: Optional[PromptVersionResponse] = None
    production_version: Optional[PromptVersionResponse] = None
    model_config = ConfigDict(from_attributes=True)


class PromptDetailResponse(PromptListResponse):
    versions: List[PromptVersionResponse]
    model_config = ConfigDict(from_attributes=True)


class DiffResponse(BaseModel):
    diff: str


class PromoteRequest(BaseModel):
    tag: str


class ForkRequest(BaseModel):
    version_id: UUID
    new_name: str
