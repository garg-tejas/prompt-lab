from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.services import ab_test_service
from app.schemas.ab_test import ABTestCreate, ABTestResponse, ABTestDetailResponse
from app.tasks.ab_test_tasks import execute_ab_test

router = APIRouter(prefix="/ab-tests", tags=["ab-tests"])


@router.post("", response_model=ABTestResponse)
async def create_ab_test(
    data: ABTestCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        ab = await ab_test_service.create_ab_test(
            db, data.name, data.eval_run_a_id, data.eval_run_b_id, user
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    execute_ab_test.delay(str(ab.id))
    return ABTestResponse.model_validate(ab)


@router.get("", response_model=List[ABTestResponse])
async def list_ab_tests(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    tests = await ab_test_service.list_ab_tests(db, user)
    return [ABTestResponse.model_validate(t) for t in tests]


@router.get("/{ab_test_id}", response_model=ABTestDetailResponse)
async def get_ab_test(
    ab_test_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ab = await ab_test_service.get_ab_test(db, ab_test_id)
    if not ab or ab.created_by != user.id:
        raise HTTPException(status_code=404, detail="AB test not found")
    return ABTestDetailResponse.model_validate(ab)


@router.delete("/{ab_test_id}")
async def delete_ab_test(
    ab_test_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ab = await ab_test_service.get_ab_test(db, ab_test_id)
    if not ab or ab.created_by != user.id:
        raise HTTPException(status_code=404, detail="AB test not found")
    await ab_test_service.delete_ab_test(db, ab)
    return {"ok": True}
