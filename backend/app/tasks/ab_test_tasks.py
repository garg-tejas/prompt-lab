import asyncio
from app.tasks.celery_app import celery_app
from app.services.ab_test_service import compute_ab_test


@celery_app.task(bind=True, max_retries=3)
def execute_ab_test(self, ab_test_id: str):
    try:
        asyncio.run(compute_ab_test_by_id(ab_test_id))
    except Exception as exc:
        raise self.retry(exc=exc, countdown=30)


async def compute_ab_test_by_id(ab_test_id: str):
    from app.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        from uuid import UUID
        await compute_ab_test(db, UUID(ab_test_id))
