"""Quick integration test for MissingGreenlet fixes."""
import asyncio
import pytest
import pytest_asyncio
from uuid import uuid4
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete

from app.database import AsyncSessionLocal
from app.models.user import User
from app.models.dataset import Dataset, DatasetRow
from app.models.prompt import Prompt, PromptVersion, PromptTag
from app.services import dataset_service, prompt_service


@pytest_asyncio.fixture
async def db():
    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def test_user(db: AsyncSession):
    user = User(
        id=uuid4(),
        clerk_id=f"test_{uuid4().hex[:8]}",
        email="test@example.com",
        name="Test User",
    )
    db.add(user)
    await db.commit()
    return user


@pytest.mark.asyncio
async def test_list_datasets_with_rows(db: AsyncSession, test_user: User):
    """Verify list_datasets eagerly loads rows (no MissingGreenlet)."""
    dataset = Dataset(name="test-ds", owner_id=test_user.id)
    db.add(dataset)
    await db.flush()
    db.add(DatasetRow(dataset_id=dataset.id, question="Q1", context="C1"))
    db.add(DatasetRow(dataset_id=dataset.id, question="Q2", context="C2"))
    await db.commit()

    datasets = await dataset_service.list_datasets(db, test_user)
    assert len(datasets) >= 1
    d = next((x for x in datasets if x.id == dataset.id), None)
    assert d is not None
    # This line previously raised MissingGreenlet
    assert len(d.rows) == 2


@pytest.mark.asyncio
async def test_create_prompt_loads_versions(db: AsyncSession, test_user: User):
    """Verify create_prompt returns prompt with versions loaded."""
    from app.schemas.prompt import PromptCreate

    data = PromptCreate(
        name="test-prompt",
        content="Hello {{name}}",
        commit_message="initial",
        tags=["tag1"],
    )
    prompt = await prompt_service.create_prompt(db, data, test_user)
    assert prompt.name == "test-prompt"
    assert len(prompt.versions) == 1
    assert prompt.versions[0].content == "Hello {{name}}"
    assert len(prompt.tags) == 1
    assert prompt.tags[0].name == "tag1"


@pytest.mark.asyncio
async def test_fork_prompt_loads_versions(db: AsyncSession, test_user: User):
    """Verify fork_prompt returns prompt with versions loaded."""
    from app.schemas.prompt import PromptCreate

    data = PromptCreate(
        name="source-prompt",
        content="Source content",
        commit_message="initial",
        tags=[],
    )
    source = await prompt_service.create_prompt(db, data, test_user)
    version_id = source.versions[0].id

    forked = await prompt_service.fork_prompt(db, source.id, version_id, "forked-prompt", test_user)
    assert forked.name == "forked-prompt"
    assert len(forked.versions) == 1
    assert forked.versions[0].content == "Source content"


@pytest.mark.asyncio
async def test_update_prompt_loads_versions(db: AsyncSession, test_user: User):
    """Verify update_prompt returns prompt with versions loaded."""
    from app.schemas.prompt import PromptCreate, PromptUpdate

    data = PromptCreate(
        name="update-prompt",
        content="Original",
        commit_message="initial",
        tags=["old-tag"],
    )
    prompt = await prompt_service.create_prompt(db, data, test_user)

    update_data = PromptUpdate(name="updated-name", tags=["new-tag"])
    updated = await prompt_service.update_prompt(db, prompt, update_data)
    assert updated.name == "updated-name"
    assert len(updated.versions) == 1
    assert len(updated.tags) == 1
    assert updated.tags[0].name == "new-tag"
