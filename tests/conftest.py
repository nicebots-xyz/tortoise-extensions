# SPDX-License-Identifier: ISC
# Copyright: 2026 NiceBots.xyz

from collections.abc import AsyncIterator

import pytest
from obstore.store import MemoryStore
from tortoise import Tortoise

from tortoise_extensions.s3 import init_storages


@pytest.fixture
async def db() -> AsyncIterator[None]:
    await Tortoise.init(
        db_url="sqlite://:memory:",
        modules={"models": ["tests.models"]},
    )
    await Tortoise.generate_schemas()
    yield
    await Tortoise.close_connections()


@pytest.fixture
def stores() -> dict[str, MemoryStore]:
    mapping = {"models": MemoryStore(), "other": MemoryStore()}
    init_storages(mapping)
    return mapping
