from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.dataset import Dataset, DatasetRow
from app.models.user import User


async def create_dataset(db: AsyncSession, data, owner: User) -> Dataset:
    dataset = Dataset(
        name=data.name,
        description=data.description,
        domain_tag=data.domain_tag,
        owner_id=owner.id,
    )
    db.add(dataset)
    await db.flush()

    for row_data in data.rows:
        row = DatasetRow(
            dataset_id=dataset.id,
            question=row_data.question,
            context=row_data.context,
            expected_answer=row_data.expected_answer,
        )
        db.add(row)

    await db.commit()
    # Re-fetch with rows loaded to avoid lazy-load error in async context
    result = await db.execute(
        select(Dataset)
        .options(selectinload(Dataset.rows))
        .where(Dataset.id == dataset.id)
    )
    return result.scalar_one()


async def get_dataset(db: AsyncSession, dataset_id: UUID) -> Optional[Dataset]:
    result = await db.execute(
        select(Dataset)
        .options(selectinload(Dataset.rows))
        .where(Dataset.id == dataset_id)
    )
    return result.scalar_one_or_none()


async def list_datasets(db: AsyncSession, owner: User) -> List[Dataset]:
    result = await db.execute(
        select(Dataset)
        .options(selectinload(Dataset.rows))
        .where(Dataset.owner_id == owner.id)
        .order_by(Dataset.created_at.desc())
    )
    return list(result.scalars().all())


async def delete_dataset(db: AsyncSession, dataset: Dataset) -> None:
    await db.delete(dataset)
    await db.commit()
