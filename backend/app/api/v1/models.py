from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.services import model_service
from app.schemas.eval import ModelEndpointCreate, ModelEndpointResponse

router = APIRouter(prefix="/models", tags=["models"])


@router.post("", response_model=ModelEndpointResponse)
async def create_model(
    data: ModelEndpointCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    model = await model_service.create_model_endpoint(db, data, user)
    return ModelEndpointResponse.model_validate(model)


@router.get("", response_model=List[ModelEndpointResponse])
async def list_models(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    models = await model_service.list_model_endpoints(db, user)
    return [ModelEndpointResponse.model_validate(m) for m in models]


@router.get("/{model_id}", response_model=ModelEndpointResponse)
async def get_model(
    model_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    model = await model_service.get_model_endpoint(db, model_id)
    if not model or model.created_by != user.id:
        raise HTTPException(status_code=404, detail="Model not found")
    return ModelEndpointResponse.model_validate(model)


@router.delete("/{model_id}")
async def delete_model(
    model_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    model = await model_service.get_model_endpoint(db, model_id)
    if not model or model.created_by != user.id:
        raise HTTPException(status_code=404, detail="Model not found")
    await model_service.delete_model_endpoint(db, model)
    return {"ok": True}
