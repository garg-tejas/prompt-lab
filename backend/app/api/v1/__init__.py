from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.prompts import router as prompts_router
from app.api.v1.datasets import router as datasets_router
from app.api.v1.models import router as models_router
from app.api.v1.eval_runs import router as eval_runs_router
from app.api.v1.ab_tests import router as ab_tests_router
from app.api.v1.analytics import router as analytics_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(prompts_router)
api_router.include_router(datasets_router)
api_router.include_router(models_router)
api_router.include_router(eval_runs_router)
api_router.include_router(ab_tests_router)
api_router.include_router(analytics_router)
