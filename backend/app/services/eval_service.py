import json
import random
import time
from datetime import datetime
from typing import List
from uuid import UUID

from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import AsyncSessionLocal
from app.models.eval import EvalRun, EvalResult, MetricScore
from app.models.prompt import PromptVersion
from app.models.dataset import Dataset, DatasetRow
from app.models.model import ModelEndpoint


JUDGE_PROMPTS = {
    "faithfulness": """You are an expert evaluator. Given a context and an answer, determine if the answer is fully supported by the context. A score of 1.0 means the answer contains no hallucinated information. A score of 0.0 means the answer is entirely unsupported.

Context:
{context}

Answer:
{answer}

Return a JSON object with:
- "score": float between 0.0 and 1.0
- "explanation": brief reasoning""",
    "answer_relevance": """You are an expert evaluator. Given a question and an answer, determine how well the answer addresses the question. A score of 1.0 means the answer is perfectly relevant and complete. A score of 0.0 means the answer is completely irrelevant.

Question:
{question}

Answer:
{answer}

Return a JSON object with:
- "score": float between 0.0 and 1.0
- "explanation": brief reasoning""",
    "context_precision": """You are an expert evaluator. Given a context and a question, determine what fraction of the provided context was actually useful for answering the question. A score of 1.0 means every piece of context was useful. A score of 0.0 means none was useful.

Context:
{context}

Question:
{question}

Return a JSON object with:
- "score": float between 0.0 and 1.0
- "explanation": brief reasoning""",
    "context_recall": """You are an expert evaluator. Given a context and a question, determine if the context contained all the information needed to answer the question. A score of 1.0 means the context was sufficient. A score of 0.0 means critical information was missing.

Context:
{context}

Question:
{question}

Return a JSON object with:
- "score": float between 0.0 and 1.0
- "explanation": brief reasoning""",
}


def fill_template(template: str, variables: dict) -> str:
    result = template
    for key, value in variables.items():
        result = result.replace(f"{{{{{key}}}}}", str(value))
    return result


async def call_llm(
    model: ModelEndpoint, messages: List[dict], temperature: float = 0.0
) -> tuple:
    client = AsyncOpenAI(base_url=model.base_url, api_key=model.api_key)
    start = time.time()
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
    judge_model: ModelEndpoint,
    retries: int = 2,
) -> dict:
    prompt = JUDGE_PROMPTS[metric_name].format(
        question=question, context=context, answer=answer
    )
    messages = [{"role": "user", "content": prompt}]

    for attempt in range(retries + 1):
        try:
            response, _ = await call_llm(judge_model, messages)
            content = response.choices[0].message.content or "{}"
            # Try to extract JSON
            try:
                data = json.loads(content)
            except json.JSONDecodeError:
                # Try finding JSON block
                start = content.find("{")
                end = content.rfind("}")
                if start != -1 and end != -1:
                    data = json.loads(content[start : end + 1])
                else:
                    raise
            return {
                "score": float(data.get("score", 0)),
                "explanation": data.get("explanation", ""),
            }
        except Exception:
            if attempt == retries:
                return {"score": 0.0, "explanation": f"Failed to evaluate {metric_name}"}
            await __import__("asyncio").sleep(1 * (2**attempt))
    return {"score": 0.0, "explanation": "Unknown error"}


async def run_eval_pipeline(eval_run_id: str) -> None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(EvalRun)
            .options(selectinload(EvalRun.results))
            .where(EvalRun.id == eval_run_id)
        )
        eval_run = result.scalar_one_or_none()
        if not eval_run:
            raise ValueError("Eval run not found")

        eval_run.status = "running"
        await db.commit()

        try:
            # Load dependencies
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

            rows = dataset.rows
            sample_size = eval_run.config.get("sample_size")
            if sample_size and 0 < sample_size < len(rows):
                rows = random.sample(rows, sample_size)

            results_summary = {
                "total_samples": len(rows),
                "metrics": {},
            }

            for row in rows:
                filled_prompt = fill_template(
                    prompt_version.content,
                    {"question": row.question, "context": row.context},
                )

                # Target model call
                response, latency_ms = await call_llm(
                    target_model,
                    [{"role": "user", "content": filled_prompt}],
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

                eval_result = EvalResult(
                    eval_run_id=eval_run.id,
                    dataset_row_id=row.id,
                    output=output,
                    latency_ms=latency_ms,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    estimated_cost=cost,
                )
                db.add(eval_result)
                await db.flush()

                # Judge metrics
                for metric_name in ["faithfulness", "answer_relevance", "context_precision", "context_recall"]:
                    judgment = await judge_metric(
                        metric_name,
                        row.question,
                        row.context,
                        output,
                        judge_model,
                        retries=eval_run.config.get("retry_count", 2),
                    )
                    score = MetricScore(
                        eval_result_id=eval_result.id,
                        metric_name=metric_name,
                        score=judgment["score"],
                        explanation=judgment["explanation"],
                        judge_model_id=judge_model.id,
                    )
                    db.add(score)
                    results_summary["metrics"].setdefault(metric_name, []).append(judgment["score"])

                await db.commit()

            # Compute summary stats
            for metric_name, scores in results_summary["metrics"].items():
                if scores:
                    results_summary["metrics"][metric_name] = {
                        "mean": round(sum(scores) / len(scores), 4),
                        "min": round(min(scores), 4),
                        "max": round(max(scores), 4),
                    }

            eval_run.status = "completed"
            eval_run.results_summary = results_summary
            eval_run.completed_at = datetime.utcnow()
            await db.commit()

        except Exception as exc:
            eval_run.status = "failed"
            eval_run.results_summary = {"error": str(exc)}
            await db.commit()
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
