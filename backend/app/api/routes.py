from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.security import get_current_user

router = APIRouter(prefix="/api/v1", tags=["v1"])

@router.get("/me")
async def get_me(user=Depends(get_current_user)):
    return user
