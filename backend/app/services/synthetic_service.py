import json
from typing import List
from uuid import UUID

from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.model import ModelEndpoint
from app.models.user import User
from app.services.model_service import get_model_endpoint


SYNTHETIC_PROMPT = """Given the following context/document, generate {num_pairs} question-answer pairs that could be used to evaluate a retrieval-augmented generation system.

Context:
{context}

For each pair, the question should require information from the context to answer correctly. Return a JSON array with objects containing:
- "question": the question string
- "context": a relevant excerpt from the context (1-3 sentences)
- "expected_answer": the correct answer

Return ONLY the JSON array, no other text."""


async def generate_qa_pairs(
    db: AsyncSession,
    context: str,
    num_pairs: int,
    model_id: UUID | None,
    user: User,
) -> List[dict]:
    if model_id:
        model = await get_model_endpoint(db, model_id)
        if not model:
            raise ValueError("Model not found")
    else:
        # Use first available judge model or fall back to OpenAI defaults
        from sqlalchemy import select
        result = await db.execute(
            select(ModelEndpoint).where(ModelEndpoint.is_judge == True).limit(1)
        )
        model = result.scalar_one_or_none()
        if not model:
            raise ValueError("No judge model available. Register one first.")

    client = AsyncOpenAI(base_url=model.base_url, api_key=model.api_key)
    prompt = SYNTHETIC_PROMPT.format(context=context, num_pairs=num_pairs)

    response = await client.chat.completions.create(
        model=model.model_name,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )

    content = response.choices[0].message.content or "[]"
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        start = content.find("[")
        end = content.rfind("]")
        if start != -1 and end != -1:
            data = json.loads(content[start : end + 1])
        else:
            raise ValueError("Failed to parse synthetic generation response")

    if not isinstance(data, list):
        raise ValueError("Expected JSON array from model")

    rows = []
    for item in data:
        rows.append({
            "question": str(item.get("question", "")).strip(),
            "context": str(item.get("context", "")).strip(),
            "expected_answer": str(item.get("expected_answer", "")).strip() or None,
        })

    return rows
