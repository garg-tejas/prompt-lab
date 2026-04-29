"""Standalone integration test for MissingGreenlet fixes.
Run with: uv run python tests/test_greenlet_standalone.py
"""
import asyncio
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models.user import User
from app.models.dataset import Dataset, DatasetRow
from app.schemas.prompt import PromptCreate, PromptUpdate
from app.services import dataset_service, prompt_service


async def test_all():
    async with AsyncSessionLocal() as db:
        # Create test user
        user = User(
            id=uuid4(),
            clerk_id=f"test_{uuid4().hex[:8]}",
            email="test@example.com",
            name="Test User",
        )
        db.add(user)
        await db.commit()
        print(f"Created user: {user.id}")

        # 1. Test list_datasets eagerly loads rows
        dataset = Dataset(name="test-ds", owner_id=user.id)
        db.add(dataset)
        await db.flush()
        db.add(DatasetRow(dataset_id=dataset.id, question="Q1", context="C1"))
        db.add(DatasetRow(dataset_id=dataset.id, question="Q2", context="C2"))
        await db.commit()

        datasets = await dataset_service.list_datasets(db, user)
        d = next((x for x in datasets if x.id == dataset.id), None)
        assert d is not None, "Dataset not found"
        assert len(d.rows) == 2, f"Expected 2 rows, got {len(d.rows)}"
        print("PASS: list_datasets eagerly loads rows")

        # 2. Test create_prompt returns prompt with versions loaded
        data = PromptCreate(
            name="test-prompt",
            content="Hello {{name}}",
            commit_message="initial",
            tags=["tag1"],
        )
        prompt = await prompt_service.create_prompt(db, data, user)
        assert prompt.name == "test-prompt"
        assert len(prompt.versions) == 1, f"Expected 1 version, got {len(prompt.versions)}"
        assert prompt.versions[0].content == "Hello {{name}}"
        assert len(prompt.tags) == 1
        assert prompt.tags[0].name == "tag1"
        print("PASS: create_prompt loads versions and tags")

        # 3. Test update_prompt returns prompt with versions loaded
        update_data = PromptUpdate(name="updated-name", tags=["new-tag"])
        updated = await prompt_service.update_prompt(db, prompt, update_data)
        assert updated.name == "updated-name"
        assert len(updated.versions) == 1, f"Expected 1 version, got {len(updated.versions)}"
        assert len(updated.tags) == 1
        assert updated.tags[0].name == "new-tag"
        print("PASS: update_prompt loads versions and tags")

        # 4. Test fork_prompt returns prompt with versions loaded
        version_id = updated.versions[0].id
        forked = await prompt_service.fork_prompt(db, updated.id, version_id, "forked-prompt", user)
        assert forked.name == "forked-prompt"
        assert len(forked.versions) == 1, f"Expected 1 version, got {len(forked.versions)}"
        assert forked.versions[0].content == "Hello {{name}}"
        print("PASS: fork_prompt loads versions")

        # Cleanup (delete in correct FK order)
        from sqlalchemy import delete
        await db.execute(delete(DatasetRow).where(DatasetRow.dataset_id == dataset.id))
        await db.execute(delete(Dataset).where(Dataset.id == dataset.id))
        # Prompts have cascade delete on versions, but we need to delete prompts first
        from app.models.prompt import Prompt, PromptVersion, prompt_tag_association
        await db.execute(delete(prompt_tag_association))
        await db.execute(delete(PromptVersion))
        await db.execute(delete(Prompt))
        await db.execute(delete(User).where(User.id == user.id))
        await db.commit()
        print("\nAll MissingGreenlet fixes verified successfully!")


if __name__ == "__main__":
    asyncio.run(test_all())
