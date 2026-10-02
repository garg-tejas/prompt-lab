from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.eval import EvalRun
from app.models.prompt import Prompt

router = APIRouter(prefix="/badges", tags=["badges"])


def _esc(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _svg(label: str, value: str, ok: bool) -> str:
    label = _esc(label)
    value = _esc(value)
    color = "#c4841d" if ok else "#8a8478"
    label_w = max(62, 7 * len(label) + 16)
    value_w = max(42, 7 * len(value) + 16)
    width = label_w + value_w
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="20" role="img" aria-label="{label}: {value}">
  <rect width="{label_w}" height="20" fill="#1c1a16"/>
  <rect x="{label_w}" width="{value_w}" height="20" fill="{color}"/>
  <text x="{label_w / 2}" y="14" fill="#f4efe6" font-family="ui-monospace,monospace" font-size="11" text-anchor="middle">{label}</text>
  <text x="{label_w + value_w / 2}" y="14" fill="#1c1a16" font-family="ui-monospace,monospace" font-size="11" text-anchor="middle">{value}</text>
</svg>"""


@router.get("/{prompt_id}.svg")
async def prompt_badge(
    prompt_id: UUID,
    metric: str = "answer_correctness",
    db: AsyncSession = Depends(get_db),
):
    prompt = await db.get(Prompt, prompt_id)
    if not prompt:
        svg = _svg("promptlab", "missing", False)
        return Response(content=svg, media_type="image/svg+xml")

    result = await db.execute(
        select(EvalRun)
        .where(EvalRun.prompt_id == prompt_id)
        .where(EvalRun.status == "completed")
        .order_by(EvalRun.completed_at.desc())
        .limit(1)
    )
    run = result.scalar_one_or_none()
    metrics = ((run.results_summary or {}).get("metrics") if run else None) or {}
    stats = metrics.get(metric)
    if not isinstance(stats, dict) or stats.get("mean") is None:
        svg = _svg(metric.replace("_", " "), "n/a", False)
    else:
        mean = stats["mean"]
        svg = _svg(metric.replace("_", " "), f"{mean:.2f}", mean >= 0.7)
    return Response(
        content=svg,
        media_type="image/svg+xml",
        headers={"Cache-Control": "no-cache"},
    )
