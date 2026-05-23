# SPDX-License-Identifier: ISC
# Copyright: 2026 NiceBots.xyz

from collections.abc import AsyncIterator

import pytest
from tortoise import Tortoise


@pytest.fixture
async def db() -> AsyncIterator[None]:
    await Tortoise.init(
        db_url="sqlite://:memory:",
        modules={"models": ["tests.models"]},
    )
    await Tortoise.generate_schemas()
    yield
    await Tortoise.close_connections()
