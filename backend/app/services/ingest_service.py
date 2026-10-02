from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.access import Trace
from app.models.model import ModelEndpoint
from app.models.prompt import Prompt, PromptVersion
from app.models.user import User
from app.services.eval_service import build_messages, call_llm, judge_metric, metrics_for_row


async def resolve_version(
    db: AsyncSession, prompt_id: UUID, version: Optional[str], owner: User
) -> PromptVersion:
    prompt = await db.get(Prompt, prompt_id)
    if not prompt or prompt.owner_id != owner.id:
        raise ValueError("Prompt not found")

    query = select(PromptVersion).where(PromptVersion.prompt_id == prompt_id)
    if not version or version == "production":
        query = query.where(PromptVersion.tag == "production")
    else:
        query = query.where(
            (PromptVersion.version_hash == version) | (PromptVersion.tag == version)
        )
    result = await db.execute(query.order_by(PromptVersion.created_at.desc()).limit(1))
    found = result.scalar_one_or_none()
    if not found:
        raise ValueError("Prompt version not found")
    return found


async def ingest_trace(
    db: AsyncSession,
    owner: User,
    prompt_id: UUID,
    version: Optional[str],
    inputs: dict,
    output: Optional[str],
    model_id: Optional[UUID],
    judge_model_id: Optional[UUID],
    score: bool,
) -> Trace:
    prompt_version = await resolve_version(db, prompt_id, version, owner)
    variables = {
        "question": inputs.get("question", ""),
        "context": inputs.get("context", ""),
        "expected_answer": inputs.get("expected_answer", "") or "",
    }
    for key, value in inputs.items():
        variables[str(key)] = "" if value is None else str(value)

    produced = output
    if produced is None:
        if not model_id:
            raise ValueError("model_id is required when output is omitted")
        model = await db.get(ModelEndpoint, model_id)
        if not model or model.created_by != owner.id:
            raise ValueError("Model not found")
        response, _ = await call_llm(model, build_messages(prompt_version, variables))
        produced = response.choices[0].message.content or ""

    scores = None
    status = "pending" if score else "stored"
    trace = Trace(
        owner_id=owner.id,
        prompt_id=prompt_id,
        prompt_version_id=prompt_version.id,
        inputs=inputs,
        output=produced,
        source="ingest",
        scores=scores,
        status=status,
    )
    db.add(trace)
    await db.commit()
    await db.refresh(trace)
    return trace


async def score_trace(trace_id: str, judge_model_id: str | None) -> None:
    from app.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        trace = await db.get(Trace, UUID(trace_id))
        if not trace or trace.status != "pending":
            return
        judge = None
        if judge_model_id:
            judge = await db.get(ModelEndpoint, UUID(judge_model_id))
        else:
            result = await db.execute(
                select(ModelEndpoint)
                .where(ModelEndpoint.created_by == trace.owner_id)
                .where(ModelEndpoint.is_judge.is_(True))
                .limit(1)
            )
            judge = result.scalar_one_or_none()
        if not judge or judge.created_by != trace.owner_id:
            trace.status = "failed"
            await db.commit()
            return
        inputs = trace.inputs or {}
        question = str(inputs.get("question", ""))
        context = str(inputs.get("context", ""))
        expected = str(inputs.get("expected_answer") or "")
        try:
            judgments = {}
            for name in metrics_for_row(expected or None):
                judgments[name] = await judge_metric(
                    name, question, context, trace.output, expected, judge
                )
            trace.scores = judgments
            trace.status = "scored"
        except Exception:
            trace.status = "failed"
        await db.commit()
