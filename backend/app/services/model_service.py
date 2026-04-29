from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.model import ModelEndpoint
from app.models.user import User


async def create_model_endpoint(db: AsyncSession, data, owner: User) -> ModelEndpoint:
    model = ModelEndpoint(
        name=data.name,
        model_name=data.model_name,
        provider=data.provider,
        base_url=data.base_url,
        api_key=data.api_key,
        context_window=data.context_window,
        cost_per_1k_input=data.cost_per_1k_input,
        cost_per_1k_output=data.cost_per_1k_output,
        is_judge=data.is_judge,
        created_by=owner.id,
    )
    db.add(model)
    await db.commit()
    await db.refresh(model)
    return model


async def get_model_endpoint(db: AsyncSession, model_id: UUID) -> Optional[ModelEndpoint]:
    result = await db.execute(select(ModelEndpoint).where(ModelEndpoint.id == model_id))
    return result.scalar_one_or_none()


async def list_model_endpoints(db: AsyncSession, owner: User) -> List[ModelEndpoint]:
    result = await db.execute(
        select(ModelEndpoint)
        .where(ModelEndpoint.created_by == owner.id)
        .order_by(ModelEndpoint.created_at.desc())
    )
    return list(result.scalars().all())


async def delete_model_endpoint(db: AsyncSession, model: ModelEndpoint) -> None:
    await db.delete(model)
    await db.commit()
