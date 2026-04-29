from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ABTestCreate(BaseModel):
    name: str
    eval_run_a_id: UUID
    eval_run_b_id: UUID


class ABTestResponse(BaseModel):
    id: UUID
    name: str
    eval_run_a_id: UUID
    eval_run_b_id: UUID
    dataset_id: UUID
    status: str
    results_summary: Optional[dict] = None
    created_by: UUID
    created_at: datetime
    completed_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class ABTestDetailResponse(ABTestResponse):
    per_sample_breakdown: Optional[list] = None
    model_config = ConfigDict(from_attributes=True)
