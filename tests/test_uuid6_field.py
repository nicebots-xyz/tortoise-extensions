# SPDX-License-Identifier: ISC
# Copyright: 2026 NiceBots.xyz

import pytest
from tortoise.models import Model
from uuid6 import UUID, uuid7

from tests.models import UuidRecord
from tortoise_extensions.uuid6 import FutureUUIDField


@pytest.fixture
def field() -> FutureUUIDField:
    return FutureUUIDField(primary_key=True)


def test_pk_default_is_uuid7(field: FutureUUIDField) -> None:
    assert field.default is uuid7


def test_to_db_value_and_python_round_trip(field: FutureUUIDField) -> None:
    value = uuid7()
    stored = field.to_db_value(value, Model)
    assert stored == str(value)
    assert field.to_python_value(stored) == value


def test_to_python_value_none(field: FutureUUIDField) -> None:
    assert field.to_python_value(None) is None


def test_to_python_value_uuid(field: FutureUUIDField) -> None:
    value = uuid7()
    assert field.to_python_value(value) is value


async def test_uuid_record_create_and_load(db: None) -> None:
    record = await UuidRecord.create()
    loaded = await UuidRecord.get(id=record.id)
    assert isinstance(loaded.id, UUID)
    assert loaded.id == record.id
    assert loaded.id.version == 7
