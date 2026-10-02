import asyncio
import hashlib
import hmac
import json
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.crypto import decrypt_secret
from app.models.access import Webhook, WebhookDelivery


async def dispatch_event(db: AsyncSession, owner_id: UUID, event: str, payload: dict) -> None:
    result = await db.execute(select(Webhook).where(Webhook.created_by == owner_id))
    hooks = list(result.scalars().all())
    if not hooks:
        return

    body = json.dumps({"event": event, "data": payload}, default=str)
    async with httpx.AsyncClient(timeout=10.0) as client:
        for hook in hooks:
            events = hook.events or []
            if events and event not in events:
                continue
            signature = hmac.new(
                decrypt_secret(hook.secret).encode(), body.encode(), hashlib.sha256
            ).hexdigest()
            attempts = 0
            last_error = None
            status = "failed"
            for delay in (0, 0.5, 1.5):
                if delay:
                    await asyncio.sleep(delay)
                attempts += 1
                try:
                    response = await client.post(
                        hook.url,
                        content=body,
                        headers={
                            "Content-Type": "application/json",
                            "X-PromptLab-Event": event,
                            "X-PromptLab-Signature": f"sha256={signature}",
                        },
                    )
                    response.raise_for_status()
                    status = "delivered"
                    last_error = None
                    break
                except httpx.HTTPError as exc:
                    last_error = str(exc)
            db.add(
                WebhookDelivery(
                    webhook_id=hook.id,
                    event=event,
                    status=status,
                    attempts=attempts,
                    last_error=last_error,
                )
            )
        await db.commit()
