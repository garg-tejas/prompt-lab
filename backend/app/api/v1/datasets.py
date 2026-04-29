from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.services import dataset_service, file_parser
from app.schemas.eval import DatasetCreate, DatasetResponse, DatasetDetailResponse, DatasetRowBase

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.post("", response_model=DatasetResponse)
async def create_dataset(
    data: DatasetCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    dataset = await dataset_service.create_dataset(db, data, user)
    return DatasetResponse(
        id=dataset.id,
        name=dataset.name,
        description=dataset.description,
        domain_tag=dataset.domain_tag,
        owner_id=dataset.owner_id,
        created_at=dataset.created_at,
        row_count=len(dataset.rows),
    )


@router.post("/upload", response_model=DatasetResponse)
async def upload_dataset(
    name: str,
    description: str = "",
    domain_tag: str = "",
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    rows = await file_parser.parse_upload_file(file)
    data = DatasetCreate(
        name=name,
        description=description or None,
        domain_tag=domain_tag or None,
        rows=[DatasetRowBase(**r) for r in rows],
    )
    dataset = await dataset_service.create_dataset(db, data, user)
    return DatasetResponse(
        id=dataset.id,
        name=dataset.name,
        description=dataset.description,
        domain_tag=dataset.domain_tag,
        owner_id=dataset.owner_id,
        created_at=dataset.created_at,
        row_count=len(dataset.rows),
    )


@router.post("/synthetic", response_model=DatasetResponse)
async def generate_synthetic(
    name: str,
    context: str,
    num_pairs: int = 5,
    description: str = "",
    domain_tag: str = "",
    model_id: UUID = None,  # type: ignore[assignment]
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    from app.services.synthetic_service import generate_qa_pairs
    rows = await generate_qa_pairs(db, context, num_pairs, model_id, user)
    data = DatasetCreate(
        name=name,
        description=description or None,
        domain_tag=domain_tag or None,
        rows=[DatasetRowBase(**r) for r in rows],
    )
    dataset = await dataset_service.create_dataset(db, data, user)
    return DatasetResponse(
        id=dataset.id,
        name=dataset.name,
        description=dataset.description,
        domain_tag=dataset.domain_tag,
        owner_id=dataset.owner_id,
        created_at=dataset.created_at,
        row_count=len(dataset.rows),
    )


@router.get("", response_model=List[DatasetResponse])
async def list_datasets(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    datasets = await dataset_service.list_datasets(db, user)
    return [
        DatasetResponse(
            id=d.id,
            name=d.name,
            description=d.description,
            domain_tag=d.domain_tag,
            owner_id=d.owner_id,
            created_at=d.created_at,
            row_count=len(d.rows) if hasattr(d, "rows") else 0,
        )
        for d in datasets
    ]


@router.get("/{dataset_id}", response_model=DatasetDetailResponse)
async def get_dataset(
    dataset_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    dataset = await dataset_service.get_dataset(db, dataset_id)
    if not dataset or dataset.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return DatasetDetailResponse(
        id=dataset.id,
        name=dataset.name,
        description=dataset.description,
        domain_tag=dataset.domain_tag,
        owner_id=dataset.owner_id,
        created_at=dataset.created_at,
        row_count=len(dataset.rows),
        rows=dataset.rows,
    )


@router.delete("/{dataset_id}")
async def delete_dataset(
    dataset_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    dataset = await dataset_service.get_dataset(db, dataset_id)
    if not dataset or dataset.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Dataset not found")
    await dataset_service.delete_dataset(db, dataset)
    return {"ok": True}
