import asyncio
import random
import time
from typing import List
from uuid import UUID
from app.core.time import utcnow

from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.crypto import decrypt_secret
from app.core.dataset_snapshot import dataset_fingerprint
from app.database import AsyncSessionLocal
from app.models.dataset import Dataset, DatasetRow
from app.models.eval import EvalRun, EvalResult, MetricScore
from app.models.model import ModelEndpoint
from app.models.prompt import PromptVersion
from app.services.metrics import (
    effective_score,
    parse_verdict_payload,
    regression_drops,
    split_context_chunks,
)


class EvalCancelled(Exception):
    pass


JUDGE_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "judgment",
        "strict": True,
        "schema": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "verdicts": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "statement": {"type": "string"},
                            "pass": {"type": "boolean"},
                        },
                        "required": ["statement", "pass"],
                    },
                },
                "explanation": {"type": "string"},
            },
            "required": ["verdicts", "explanation"],
        },
    },
}

JUDGE_PROMPTS = {
    "faithfulness": """Break the answer into atomic claims. For each claim, pass is true only when the context supports it. Do not give a holistic score.

Context:
{context}

Answer:
{answer}

Return JSON with "verdicts" (statement, pass) and "explanation".""",
    "answer_relevance": """List what the question asks for. For each part, pass is true only when the answer addresses it.

Question:
{question}

Answer:
{answer}

Return JSON with "verdicts" (statement, pass) and "explanation".""",
    "context_precision": """Each block below is one retrieved chunk. Return one verdict per block, in order. pass is true only when that chunk helps answer the question.

Question:
{question}

Chunks:
{chunks}

Return JSON with "verdicts" (statement, pass) and "explanation".""",
    "context_recall": """Break the ground-truth answer into facts. For each fact, pass is true only when the context contains it.

Context:
{context}

Question:
{question}

Ground-truth answer:
{expected_answer}

Return JSON with "verdicts" (statement, pass) and "explanation".""",
    "answer_correctness": """Break the ground-truth answer into facts. For each fact, pass is true only when the model answer states it without contradiction.

Question:
{question}

Model answer:
{answer}

Ground-truth answer:
{expected_answer}

Return JSON with "verdicts" (statement, pass) and "explanation".""",
}


def fill_template(template: str, variables: dict) -> str:
    result = template
    for key, value in variables.items():
        result = result.replace(f"{{{{{key}}}}}", "" if value is None else str(value))
    return result


def row_variables(row: DatasetRow) -> dict:
    data = {
        "question": row.question,
        "context": row.context,
        "expected_answer": row.expected_answer or "",
    }
    extras = row.extras or {}
    if isinstance(extras, dict):
        for key, value in extras.items():
            data[str(key)] = "" if value is None else str(value)
    return data


def build_messages(prompt_version: PromptVersion, variables: dict) -> List[dict]:
    messages = []
    if prompt_version.system_content:
        messages.append(
            {
                "role": "system",
                "content": fill_template(prompt_version.system_content, variables),
            }
        )
    for turn in prompt_version.messages or []:
        if not isinstance(turn, dict):
            continue
        role = turn.get("role") or "user"
        content = turn.get("content") or ""
        messages.append({"role": role, "content": fill_template(str(content), variables)})
    messages.append(
        {"role": "user", "content": fill_template(prompt_version.content, variables)}
    )
    return messages


def _parse_judgment(content: str) -> dict:
    return parse_verdict_payload(content)


async def call_llm(
    model: ModelEndpoint,
    messages: List[dict],
    temperature: float = 0.0,
    response_format: dict | None = None,
) -> tuple:
    client = AsyncOpenAI(base_url=model.base_url, api_key=decrypt_secret(model.api_key))
    kwargs = {}
    if response_format is not None:
        kwargs["response_format"] = response_format
    start = time.time()
    try:
        response = await client.chat.completions.create(
            model=model.model_name,
            messages=messages,  # type: ignore[arg-type]
            temperature=temperature,
            **kwargs,
        )
    except Exception:
        if response_format is None:
            raise
        response = await client.chat.completions.create(
            model=model.model_name,
            messages=messages,  # type: ignore[arg-type]
            temperature=temperature,
        )
    latency_ms = (time.time() - start) * 1000
    return response, latency_ms


async def judge_metric(
    metric_name: str,
    question: str,
    context: str,
    answer: str,
    expected_answer: str,
    judge_model: ModelEndpoint,
    retries: int = 2,
) -> dict:
    chunks = "\n".join(
        f"[{index}] {chunk}" for index, chunk in enumerate(split_context_chunks(context), start=1)
    )
    prompt = JUDGE_PROMPTS[metric_name].format(
        question=question,
        context=context,
        chunks=chunks or context,
        answer=answer,
        expected_answer=expected_answer,
    )
    messages = [{"role": "user", "content": prompt}]

    for attempt in range(retries + 1):
        try:
            response, _ = await call_llm(
                judge_model, messages, response_format=JUDGE_SCHEMA
            )
            content = response.choices[0].message.content or "{}"
            parsed = _parse_judgment(content)
            usage = response.usage
            parsed["input_tokens"] = usage.prompt_tokens if usage else 0
            parsed["output_tokens"] = usage.completion_tokens if usage else 0
            return parsed
        except Exception:
            if attempt == retries:
                return {
                    "score": None,
                    "explanation": f"Failed to evaluate {metric_name}",
                    "input_tokens": 0,
                    "output_tokens": 0,
                }
            await asyncio.sleep(1 * (2**attempt))
    return {"score": None, "explanation": "Unknown error", "input_tokens": 0, "output_tokens": 0}


def metrics_for_row(expected_answer: str | None) -> List[str]:
    names = ["faithfulness", "answer_relevance", "context_precision"]
    if expected_answer:
        names.extend(["context_recall", "answer_correctness"])
    return names


async def _is_cancelled(eval_run_id: str) -> bool:
    async with AsyncSessionLocal() as session:
        run = await session.get(EvalRun, eval_run_id)
        return run is None or run.status == "cancelled"


def _summarize(scores_by_metric: dict, total: int, failed: int, completed: int, eligible_rows=None, input_fingerprint=None) -> dict:
    metrics = {}
    judge_errors = 0
    for metric_name, scores in scores_by_metric.items():
        numeric = [score for score in scores if score is not None]
        judge_errors += len(scores) - len(numeric)
        if numeric:
            metrics[metric_name] = {
                "mean": round(sum(numeric) / len(numeric), 4),
                "min": round(min(numeric), 4),
                "max": round(max(numeric), 4),
                "n": len(numeric),
                "errors": len(scores) - len(numeric),
            }
    return {
        "total_samples": total,
        "failed_rows": failed,
        "judge_errors": judge_errors,
        "progress": {"completed": completed, "total": total, "failed": failed},
        "metrics": metrics,
        **({"metric_eligible_rows": eligible_rows} if eligible_rows is not None else {}),
        **({"dataset_fingerprint": input_fingerprint} if input_fingerprint is not None else {}),
    }


async def _detect_anomaly(db: AsyncSession, eval_run: EvalRun, summary: dict) -> dict | None:
    threshold = float((eval_run.config or {}).get("anomaly_drop", 0.1))
    result = await db.execute(
        select(EvalRun)
        .where(EvalRun.prompt_id == eval_run.prompt_id)
        .where(EvalRun.dataset_id == eval_run.dataset_id)
        .where(EvalRun.model_id == eval_run.model_id)
        .where(EvalRun.status == "completed")
        .where(EvalRun.id != eval_run.id)
        .order_by(EvalRun.completed_at.desc())
        .limit(5)
    )
    previous_runs = list(result.scalars().all())
    history = [
        (run.results_summary or {}).get("metrics") or {}
        for run in previous_runs
        if run.results_summary
    ]
    drops = regression_drops(summary["metrics"], history, threshold)
    if not drops:
        return None
    return {
        "previous_run_id": str(previous_runs[0].id),
        "baseline_runs": len(history),
        "threshold": threshold,
        "drops": drops,
    }


async def run_eval_pipeline(eval_run_id: str) -> None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(EvalRun).where(EvalRun.id == eval_run_id))
        eval_run = result.scalar_one_or_none()
        if not eval_run:
            raise ValueError("Eval run not found")
        if eval_run.status == "cancelled":
            return

        eval_run.status = "running"
        await db.commit()

        try:
            pv_result = await db.execute(
                select(PromptVersion).where(PromptVersion.id == eval_run.prompt_version_id)
            )
            prompt_version = pv_result.scalar_one()

            ds_result = await db.execute(
                select(Dataset)
                .options(selectinload(Dataset.rows))
                .where(Dataset.id == eval_run.dataset_id)
            )
            dataset = ds_result.scalar_one()

            model_result = await db.execute(
                select(ModelEndpoint).where(ModelEndpoint.id == eval_run.model_id)
            )
            target_model = model_result.scalar_one()

            judge_result = await db.execute(
                select(ModelEndpoint).where(ModelEndpoint.id == eval_run.judge_model_id)
            )
            judge_model = judge_result.scalar_one()

            done_result = await db.execute(
                select(EvalResult.dataset_row_id).where(EvalResult.eval_run_id == eval_run.id)
            )
            done_ids = set(done_result.scalars().all())

            rows = list(dataset.rows)
            sample_size = (eval_run.config or {}).get("sample_size")
            if sample_size and 0 < sample_size < len(rows):
                rows = random.Random(str(eval_run.id)).sample(rows, sample_size)

            total = len(rows)
            input_fingerprint = dataset_fingerprint(rows)
            previous_fingerprint = (eval_run.results_summary or {}).get("dataset_fingerprint")
            if done_ids and previous_fingerprint is not None and previous_fingerprint != input_fingerprint:
                raise ValueError("Dataset contents changed during retry; create a new evaluation run")
            if done_ids and previous_fingerprint is None:
                input_fingerprint = None
            eligible_rows = {name: [] for name in metrics_for_row("reference")}
            for row in rows:
                for name in metrics_for_row(row.expected_answer):
                    eligible_rows[name].append(str(row.id))
            eligible_rows = {name: sorted(ids) for name, ids in eligible_rows.items()}
            previous_eligibility = (eval_run.results_summary or {}).get("metric_eligible_rows")
            if done_ids and previous_eligibility is not None and previous_eligibility != eligible_rows:
                raise ValueError("Dataset metric applicability changed during retry; create a new evaluation run")
            if not done_ids or previous_eligibility is not None:
                eval_run.results_summary = {
                    **(eval_run.results_summary or {}),
                    "metric_eligible_rows": eligible_rows,
                    **({"dataset_fingerprint": input_fingerprint} if input_fingerprint is not None else {}),
                }
                await db.commit()
            else:
                # A resumed historical run has no immutable eligibility record.
                eligible_rows = None
            pending = [row for row in rows if row.id not in done_ids]
            completed = total - len(pending)
            failed = 0
            batch_size: int = (eval_run.config or {}).get("concurrency") or 5
            retry_count: int = (eval_run.config or {}).get("retry_count", 2)
            scores_by_metric: dict = {}

            # Fold scores already stored so a retry still summarizes the whole run.
            if done_ids:
                existing = await db.execute(
                    select(MetricScore)
                    .join(EvalResult)
                    .where(EvalResult.eval_run_id == eval_run.id)
                )
                for score in existing.scalars().all():
                    value = effective_score(score.score, score.human_score)
                    scores_by_metric.setdefault(score.metric_name, []).append(value)

            async def process_row(row: DatasetRow) -> dict:
                if await _is_cancelled(str(eval_run.id)):
                    raise EvalCancelled()
                variables = row_variables(row)
                response, latency_ms = await call_llm(
                    target_model, build_messages(prompt_version, variables)
                )
                output = response.choices[0].message.content or ""
                input_tokens = response.usage.prompt_tokens if response.usage else 0
                output_tokens = response.usage.completion_tokens if response.usage else 0
                cost = 0.0
                if target_model.cost_per_1k_input and target_model.cost_per_1k_output:
                    cost = (
                        input_tokens / 1000 * target_model.cost_per_1k_input
                        + output_tokens / 1000 * target_model.cost_per_1k_output
                    )

                metric_names = metrics_for_row(row.expected_answer)
                judgments = await asyncio.gather(
                    *[
                        judge_metric(
                            name,
                            row.question,
                            row.context,
                            output,
                            row.expected_answer or "",
                            judge_model,
                            retries=retry_count,
                        )
                        for name in metric_names
                    ]
                )
                if judge_model.cost_per_1k_input and judge_model.cost_per_1k_output:
                    for judgment in judgments:
                        cost += (
                            (judgment.get("input_tokens") or 0) / 1000 * judge_model.cost_per_1k_input
                            + (judgment.get("output_tokens") or 0) / 1000 * judge_model.cost_per_1k_output
                        )
                return {
                    "row": row,
                    "output": output,
                    "latency_ms": latency_ms,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "cost": cost,
                    "judgments": dict(zip(metric_names, judgments)),
                }

            for batch_start in range(0, len(pending), batch_size):
                if await _is_cancelled(str(eval_run.id)):
                    raise EvalCancelled()
                batch = pending[batch_start : batch_start + batch_size]
                batch_results = await asyncio.gather(
                    *[process_row(row) for row in batch],
                    return_exceptions=True,
                )
                for item in batch_results:
                    if isinstance(item, EvalCancelled):
                        raise EvalCancelled()
                    if isinstance(item, Exception):
                        failed += 1
                        continue
                    row = item["row"]
                    eval_result = EvalResult(
                        eval_run_id=eval_run.id,
                        dataset_row_id=row.id,
                        output=item["output"],
                        latency_ms=item["latency_ms"],
                        input_tokens=item["input_tokens"],
                        output_tokens=item["output_tokens"],
                        estimated_cost=item["cost"],
                    )
                    db.add(eval_result)
                    await db.flush()
                    for metric_name, judgment in item["judgments"].items():
                        db.add(
                            MetricScore(
                                eval_result_id=eval_result.id,
                                metric_name=metric_name,
                                score=judgment["score"],
                                explanation=judgment["explanation"],
                                judge_model_id=judge_model.id,
                            )
                        )
                        scores_by_metric.setdefault(metric_name, []).append(judgment["score"])
                    completed += 1

                eval_run.results_summary = _summarize(scores_by_metric, total, failed, completed, eligible_rows, input_fingerprint)
                await db.commit()

            if await _is_cancelled(str(eval_run.id)):
                raise EvalCancelled()
            summary = _summarize(scores_by_metric, total, failed, completed, eligible_rows, input_fingerprint)
            anomaly = await _detect_anomaly(db, eval_run, summary)
            if anomaly:
                summary["anomaly"] = anomaly
            eval_run.status = "completed"
            eval_run.results_summary = summary
            eval_run.completed_at = utcnow()
            await db.commit()

            from app.services.webhook_service import dispatch_event

            payload = {
                "eval_run_id": str(eval_run.id),
                "name": eval_run.name,
                "status": eval_run.status,
                "results_summary": summary,
            }
            await dispatch_event(db, eval_run.created_by, "eval.completed", payload)
            if anomaly:
                await dispatch_event(db, eval_run.created_by, "eval.anomaly", payload)

        except EvalCancelled:
            eval_run.status = "cancelled"
            await db.commit()
            return
        except Exception as exc:
            eval_run.status = "failed"
            eval_run.results_summary = {
                **(eval_run.results_summary or {}),
                "error": str(exc),
            }
            await db.commit()
            from app.services.webhook_service import dispatch_event

            await dispatch_event(
                db,
                eval_run.created_by,
                "eval.failed",
                {"eval_run_id": str(eval_run.id), "name": eval_run.name, "error": str(exc)},
            )
            raise


async def create_eval_run(db: AsyncSession, data, owner) -> EvalRun:
    eval_run = EvalRun(
        name=data.name,
        prompt_id=data.prompt_id,
        prompt_version_id=data.prompt_version_id,
        dataset_id=data.dataset_id,
        model_id=data.model_id,
        judge_model_id=data.judge_model_id,
        config=data.config.model_dump() if hasattr(data.config, "model_dump") else dict(data.config),
        created_by=owner.id,
    )
    db.add(eval_run)
    await db.commit()
    await db.refresh(eval_run)
    return eval_run


async def get_eval_run(db: AsyncSession, eval_run_id: UUID) -> EvalRun:
    result = await db.execute(
        select(EvalRun)
        .options(selectinload(EvalRun.results).selectinload(EvalResult.scores))
        .where(EvalRun.id == eval_run_id)
    )
    return result.scalar_one_or_none()


async def list_eval_runs(db: AsyncSession, owner) -> List[EvalRun]:
    result = await db.execute(
        select(EvalRun)
        .where(EvalRun.created_by == owner.id)
        .order_by(EvalRun.created_at.desc())
    )
    return list(result.scalars().all())


async def cancel_eval_run(db: AsyncSession, eval_run: EvalRun) -> EvalRun:
    if eval_run.status in ("completed", "failed", "cancelled"):
        return eval_run
    eval_run.status = "cancelled"
    await db.commit()
    await db.refresh(eval_run)
    return eval_run
