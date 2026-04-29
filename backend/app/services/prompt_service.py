import difflib
import hashlib
import time
import re
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload

from app.models.prompt import Prompt, PromptVersion, PromptTag
from app.models.user import User


def extract_variables(content: str) -> List[str]:
    matches = re.findall(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}", content)
    return list(dict.fromkeys(matches))


def generate_version_hash(content: str) -> str:
    return hashlib.sha256(f"{content}{time.time()}".encode()).hexdigest()[:7]


def compute_diff(content_a: str, content_b: str) -> str:
    a_lines = content_a.splitlines(keepends=True)
    b_lines = content_b.splitlines(keepends=True)
    diff = list(
        difflib.unified_diff(
            a_lines, b_lines, fromfile="a", tofile="b", lineterm=""
        )
    )
    return "\n".join(diff)


async def get_or_create_tags(db: AsyncSession, tag_names: List[str]) -> List[PromptTag]:
    tags: List[PromptTag] = []
    for name in tag_names:
        result = await db.execute(select(PromptTag).where(PromptTag.name == name))
        tag = result.scalar_one_or_none()
        if not tag:
            tag = PromptTag(name=name)
            db.add(tag)
            await db.flush()
        tags.append(tag)
    return tags


async def create_prompt(db: AsyncSession, data, owner: User) -> Prompt:
    prompt = Prompt(
        name=data.name,
        description=data.description,
        owner_id=owner.id,
    )
    db.add(prompt)
    await db.flush()

    version = PromptVersion(
        prompt_id=prompt.id,
        version_hash=generate_version_hash(data.content),
        commit_message=data.commit_message,
        content=data.content,
        variables=extract_variables(data.content),
        tag="production",
        created_by=owner.id,
    )
    db.add(version)

    if data.tags:
        tags = await get_or_create_tags(db, data.tags)
        prompt.tags.extend(tags)

    await db.commit()
    await db.refresh(prompt)
    return prompt


async def get_prompt(db: AsyncSession, prompt_id: UUID) -> Optional[Prompt]:
    result = await db.execute(
        select(Prompt)
        .options(selectinload(Prompt.tags), selectinload(Prompt.versions))
        .where(Prompt.id == prompt_id)
    )
    return result.scalar_one_or_none()


async def list_prompts(db: AsyncSession, owner: User) -> List[Prompt]:
    result = await db.execute(
        select(Prompt)
        .options(selectinload(Prompt.tags), selectinload(Prompt.versions))
        .where(Prompt.owner_id == owner.id)
        .order_by(Prompt.updated_at.desc())
    )
    return list(result.scalars().all())


async def update_prompt(
    db: AsyncSession, prompt: Prompt, data
) -> Prompt:
    if data.name is not None:
        prompt.name = data.name
    if data.description is not None:
        prompt.description = data.description
    if data.tags is not None:
        tags = await get_or_create_tags(db, data.tags)
        prompt.tags = tags
    prompt.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(prompt)
    return prompt


async def create_version(
    db: AsyncSession, prompt_id: UUID, content: str, commit_message: str, user: User
) -> PromptVersion:
    version = PromptVersion(
        prompt_id=prompt_id,
        version_hash=generate_version_hash(content),
        commit_message=commit_message,
        content=content,
        variables=extract_variables(content),
        tag="dev",
        created_by=user.id,
    )
    db.add(version)
    await db.commit()
    await db.refresh(version)

    # Update prompt timestamp
    result = await db.execute(select(Prompt).where(Prompt.id == prompt_id))
    prompt = result.scalar_one_or_none()
    if prompt:
        prompt.updated_at = datetime.utcnow()
        await db.commit()

    return version


async def promote_version(
    db: AsyncSession, prompt_id: UUID, version_id: UUID, tag: str
) -> PromptVersion:
    if tag not in ("dev", "staging", "production"):
        raise ValueError("Invalid tag. Must be dev, staging, or production")

    if tag == "production":
        result = await db.execute(
            select(PromptVersion).where(
                and_(
                    PromptVersion.prompt_id == prompt_id,
                    PromptVersion.tag == "production",
                )
            )
        )
        current_prod = result.scalar_one_or_none()
        if current_prod:
            current_prod.tag = None
            await db.flush()

    result = await db.execute(
        select(PromptVersion).where(
            and_(
                PromptVersion.id == version_id,
                PromptVersion.prompt_id == prompt_id,
            )
        )
    )
    version = result.scalar_one_or_none()
    if not version:
        raise ValueError("Version not found")

    version.tag = tag
    await db.commit()
    await db.refresh(version)
    return version


async def fork_prompt(
    db: AsyncSession, prompt_id: UUID, version_id: UUID, new_name: str, user: User
) -> Prompt:
    result = await db.execute(
        select(PromptVersion).where(
            and_(
                PromptVersion.id == version_id,
                PromptVersion.prompt_id == prompt_id,
            )
        )
    )
    source_version = result.scalar_one_or_none()
    if not source_version:
        raise ValueError("Source version not found")

    new_prompt = Prompt(
        name=new_name,
        description=f"Forked from {prompt_id} (version {source_version.version_hash})",
        owner_id=user.id,
    )
    db.add(new_prompt)
    await db.flush()

    new_version = PromptVersion(
        prompt_id=new_prompt.id,
        version_hash=generate_version_hash(source_version.content),
        commit_message=f"Forked from version {source_version.version_hash}",
        content=source_version.content,
        variables=source_version.variables,
        tag="production",
        created_by=user.id,
    )
    db.add(new_version)
    await db.commit()
    await db.refresh(new_prompt)
    return new_prompt
