from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


# Dataset Schemas
class DatasetRowBase(BaseModel):
    question: str
    context: str
    expected_answer: Optional[str] = None


class DatasetRowResponse(DatasetRowBase):
    id: UUID
    dataset_id: UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class DatasetBase(BaseModel):
    name: str
    description: Optional[str] = None
    domain_tag: Optional[str] = None


class DatasetCreate(DatasetBase):
    rows: List[DatasetRowBase] = []


class DatasetResponse(DatasetBase):
    id: UUID
    owner_id: UUID
    created_at: datetime
    row_count: int
    model_config = ConfigDict(from_attributes=True)


class DatasetDetailResponse(DatasetResponse):
    rows: List[DatasetRowResponse]
    model_config = ConfigDict(from_attributes=True)


# ModelEndpoint Schemas
class ModelEndpointBase(BaseModel):
    name: str
    model_name: str
    provider: str
    base_url: str
    context_window: Optional[int] = None
    cost_per_1k_input: Optional[float] = None
    cost_per_1k_output: Optional[float] = None
    is_judge: bool = False


class ModelEndpointCreate(ModelEndpointBase):
    api_key: str


class ModelEndpointResponse(ModelEndpointBase):
    id: UUID
    created_by: UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# EvalRun Schemas
class EvalConfig(BaseModel):
    sample_size: Optional[int] = None
    concurrency: int = 5
    retry_count: int = 2


class EvalRunBase(BaseModel):
    name: str
    prompt_id: UUID
    prompt_version_id: UUID
    dataset_id: UUID
    model_id: UUID
    judge_model_id: UUID


class EvalRunCreate(EvalRunBase):
    config: EvalConfig = EvalConfig()


class EvalRunResponse(EvalRunBase):
    id: UUID
    status: str
    config: dict
    results_summary: Optional[dict] = None
    created_by: UUID
    created_at: datetime
    completed_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class EvalRunListResponse(BaseModel):
    id: UUID
    name: str
    status: str
    created_at: datetime
    prompt_name: str
    model_name: str
    model_config = ConfigDict(from_attributes=True)


# EvalResult / Metric Schemas
class MetricScoreResponse(BaseModel):
    id: UUID
    metric_name: str
    score: float
    explanation: Optional[str] = None
    judge_model_id: UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class EvalResultResponse(BaseModel):
    id: UUID
    dataset_row_id: UUID
    output: str
    latency_ms: float
    input_tokens: int
    output_tokens: int
    estimated_cost: float
    created_at: datetime
    scores: List[MetricScoreResponse]
    model_config = ConfigDict(from_attributes=True)


class EvalRunDetailResponse(EvalRunResponse):
    results: List[EvalResultResponse]
    model_config = ConfigDict(from_attributes=True)
