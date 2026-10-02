import hashlib
import secrets
from datetime import datetime
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, HttpUrl
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.crypto import encrypt_secret
from app.api.deps import get_current_user
from app.database import get_db
from app.models.access import ApiToken, Trace, Webhook, WebhookDelivery
from app.models.user import User

router = APIRouter(tags=["access"])

DEFAULT_EVENTS = ["eval.completed", "eval.failed", "eval.anomaly"]


class TokenCreate(BaseModel):
    name: str


class TokenCreated(BaseModel):
    id: UUID
    name: str
    token: str
    created_at: datetime


class TokenResponse(BaseModel):
    id: UUID
    name: str
    token_prefix: str
    created_at: datetime
    last_used_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)


class WebhookCreate(BaseModel):
    url: HttpUrl
    events: List[str] = DEFAULT_EVENTS


class WebhookCreated(BaseModel):
    id: UUID
    url: str
    secret: str
    events: List[str]
    created_at: datetime


class WebhookResponse(BaseModel):
    id: UUID
    url: str
    events: List[str]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class TraceResponse(BaseModel):
    id: UUID
    prompt_id: UUID | None
    prompt_version_id: UUID | None
    inputs: dict
    output: str
    source: str
    scores: dict | None
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class TracePage(BaseModel):
    items: List[TraceResponse]
    total: int
    offset: int
    limit: int


@router.post("/tokens", response_model=TokenCreated)
async def create_token(
    data: TokenCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    raw = f"pl_{secrets.token_urlsafe(32)}"
    token = ApiToken(
        name=data.name,
        token_prefix=raw[:11],
        token_hash=hashlib.sha256(raw.encode()).hexdigest(),
        created_by=user.id,
    )
    db.add(token)
    await db.commit()
    await db.refresh(token)
    return TokenCreated(id=token.id, name=token.name, token=raw, created_at=token.created_at)


@router.get("/tokens", response_model=List[TokenResponse])
async def list_tokens(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(ApiToken).where(ApiToken.created_by == user.id).order_by(ApiToken.created_at.desc())
    )
    return list(result.scalars().all())


@router.delete("/tokens/{token_id}")
async def delete_token(
    token_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    token = await db.get(ApiToken, token_id)
    if not token or token.created_by != user.id:
        raise HTTPException(status_code=404, detail="Token not found")
    await db.delete(token)
    await db.commit()
    return {"ok": True}


@router.post("/webhooks", response_model=WebhookCreated)
async def create_webhook(
    data: WebhookCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    secret = secrets.token_urlsafe(24)
    hook = Webhook(
        url=str(data.url),
        secret=encrypt_secret(secret),
        events=data.events or DEFAULT_EVENTS,
        created_by=user.id,
    )
    db.add(hook)
    await db.commit()
    await db.refresh(hook)
    return WebhookCreated(
        id=hook.id,
        url=hook.url,
        secret=secret,
        events=hook.events,
        created_at=hook.created_at,
    )


@router.get("/webhooks", response_model=List[WebhookResponse])
async def list_webhooks(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Webhook).where(Webhook.created_by == user.id).order_by(Webhook.created_at.desc())
    )
    return list(result.scalars().all())


@router.delete("/webhooks/{webhook_id}")
async def delete_webhook(
    webhook_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    hook = await db.get(Webhook, webhook_id)
    if not hook or hook.created_by != user.id:
        raise HTTPException(status_code=404, detail="Webhook not found")
    await db.delete(hook)
    await db.commit()
    return {"ok": True}


@router.get("/webhooks/{webhook_id}/deliveries")
async def list_deliveries(
    webhook_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    hook = await db.get(Webhook, webhook_id)
    if not hook or hook.created_by != user.id:
        raise HTTPException(status_code=404, detail="Webhook not found")
    result = await db.execute(
        select(WebhookDelivery)
        .where(WebhookDelivery.webhook_id == webhook_id)
        .order_by(WebhookDelivery.created_at.desc())
        .limit(20)
    )
    rows = result.scalars().all()
    return [
        {
            "id": str(row.id),
            "event": row.event,
            "status": row.status,
            "attempts": row.attempts,
            "last_error": row.last_error,
            "created_at": row.created_at,
        }
        for row in rows
    ]


@router.get("/traces", response_model=TracePage)
async def list_traces(
    offset: int = 0,
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    total = await db.scalar(
        select(func.count()).select_from(Trace).where(Trace.owner_id == user.id)
    )
    result = await db.execute(
        select(Trace)
        .where(Trace.owner_id == user.id)
        .order_by(Trace.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    return TracePage(
        items=list(result.scalars().all()),
        total=total or 0,
        offset=offset,
        limit=limit,
    )
