import asyncio
from app.tasks.celery_app import celery_app
from app.services.eval_service import run_eval_pipeline


@celery_app.task(bind=True, max_retries=3)
def execute_eval_run(self, eval_run_id: str):
    try:
        asyncio.run(run_eval_pipeline(eval_run_id))
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)
