import asyncio
from app.tasks.celery_app import celery_app
from app.services.eval_service import EvalCancelled, run_eval_pipeline
from app.services.ingest_service import score_trace

_loop: asyncio.AbstractEventLoop | None = None


def _worker_loop() -> asyncio.AbstractEventLoop:
    """One loop per worker process so the async engine is not rebound per task."""
    global _loop
    if _loop is None or _loop.is_closed():
        _loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_loop)
    return _loop


@celery_app.task(bind=True, max_retries=3)
def execute_eval_run(self, eval_run_id: str):
    try:
        _worker_loop().run_until_complete(run_eval_pipeline(eval_run_id))
    except EvalCancelled:
        return
    except ValueError:
        return
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)


@celery_app.task
def score_trace_task(trace_id: str, judge_model_id: str | None = None):
    _worker_loop().run_until_complete(score_trace(trace_id, judge_model_id))
