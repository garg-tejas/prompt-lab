from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.services import prompt_service
from app.schemas.prompt import (
    PromptCreate,
    PromptDetailResponse,
    PromptListResponse,
    PromptTagResponse,
    PromptUpdate,
    PromptVersionCreate,
    PromptVersionResponse,
    DiffResponse,
    PromoteRequest,
    ForkRequest,
)

router = APIRouter(prefix="/prompts", tags=["prompts"])


@router.post("", response_model=PromptDetailResponse)
async def create_prompt(
    data: PromptCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    prompt = await prompt_service.create_prompt(db, data, user)
    return _build_prompt_detail(prompt)


@router.get("", response_model=List[PromptListResponse])
async def list_prompts(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    prompts = await prompt_service.list_prompts(db, user)
    return [_build_prompt_list(p) for p in prompts]


@router.get("/{prompt_id}", response_model=PromptDetailResponse)
async def get_prompt(
    prompt_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    prompt = await prompt_service.get_prompt(db, prompt_id)
    if not prompt or prompt.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return _build_prompt_detail(prompt)


@router.patch("/{prompt_id}", response_model=PromptDetailResponse)
async def update_prompt(
    prompt_id: UUID,
    data: PromptUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    prompt = await prompt_service.get_prompt(db, prompt_id)
    if not prompt or prompt.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Prompt not found")
    prompt = await prompt_service.update_prompt(db, prompt, data)
    return _build_prompt_detail(prompt)


@router.post("/{prompt_id}/versions", response_model=PromptVersionResponse)
async def create_version(
    prompt_id: UUID,
    data: PromptVersionCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    prompt = await prompt_service.get_prompt(db, prompt_id)
    if not prompt or prompt.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Prompt not found")
    version = await prompt_service.create_version(
        db, prompt_id, data.content, data.commit_message, user
    )
    return PromptVersionResponse.model_validate(version)


@router.post("/{prompt_id}/versions/{version_id}/promote", response_model=PromptVersionResponse)
async def promote_version(
    prompt_id: UUID,
    version_id: UUID,
    body: PromoteRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    prompt = await prompt_service.get_prompt(db, prompt_id)
    if not prompt or prompt.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Prompt not found")
    try:
        version = await prompt_service.promote_version(db, prompt_id, version_id, body.tag)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return PromptVersionResponse.model_validate(version)


@router.get("/{prompt_id}/versions/{version_id}/diff/{other_version_id}", response_model=DiffResponse)
async def diff_versions(
    prompt_id: UUID,
    version_id: UUID,
    other_version_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    prompt = await prompt_service.get_prompt(db, prompt_id)
    if not prompt or prompt.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Prompt not found")

    version_a = next((v for v in prompt.versions if str(v.id) == str(version_id)), None)
    version_b = next((v for v in prompt.versions if str(v.id) == str(other_version_id)), None)

    if not version_a or not version_b:
        raise HTTPException(status_code=404, detail="Version not found")

    diff = prompt_service.compute_diff(version_a.content, version_b.content)
    return DiffResponse(diff=diff)


@router.post("/{prompt_id}/fork", response_model=PromptDetailResponse)
async def fork_prompt(
    prompt_id: UUID,
    body: ForkRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        new_prompt = await prompt_service.fork_prompt(db, prompt_id, body.version_id, body.new_name, user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _build_prompt_detail(new_prompt)


def _build_prompt_list(prompt) -> PromptListResponse:
    versions = sorted(prompt.versions, key=lambda v: v.created_at, reverse=True)
    latest = versions[0] if versions else None
    production = next((v for v in versions if v.tag == "production"), None)
    return PromptListResponse(
        id=prompt.id,
        name=prompt.name,
        description=prompt.description,
        owner_id=prompt.owner_id,
        tags=[PromptTagResponse.model_validate(t) for t in prompt.tags],
        created_at=prompt.created_at,
        updated_at=prompt.updated_at,
        version_count=len(versions),
        latest_version=PromptVersionResponse.model_validate(latest) if latest else None,
        production_version=PromptVersionResponse.model_validate(production) if production else None,
    )


def _build_prompt_detail(prompt) -> PromptDetailResponse:
    base = _build_prompt_list(prompt)
    versions = sorted(prompt.versions, key=lambda v: v.created_at, reverse=True)
    return PromptDetailResponse(
        **base.model_dump(),
        versions=[PromptVersionResponse.model_validate(v) for v in versions],
    )
