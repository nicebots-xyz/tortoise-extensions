# SPDX-License-Identifier: ISC
# Copyright: 2026 NiceBots.xyz

import json

import pytest
from tortoise.models import Model

from tests.models import PydanticRecord, SamplePayload
from tortoise_extensions.pydantic import PydanticJSONField


@pytest.fixture
def field() -> PydanticJSONField[SamplePayload]:
    return PydanticJSONField(SamplePayload)


def test_to_python_value_from_dict(field: PydanticJSONField[SamplePayload]) -> None:
    result = field.to_python_value({"name": "alpha", "count": 2})
    assert result == SamplePayload(name="alpha", count=2)


def test_to_python_value_from_json_str(field: PydanticJSONField[SamplePayload]) -> None:
    raw = json.dumps({"name": "beta", "count": 1})
    result = field.to_python_value(raw)
    assert result == SamplePayload(name="beta", count=1)


def test_to_python_value_from_bytes(field: PydanticJSONField[SamplePayload]) -> None:
    raw = json.dumps({"name": "gamma"}).encode()
    result = field.to_python_value(raw)
    assert result == SamplePayload(name="gamma", count=0)


def test_to_python_value_none(field: PydanticJSONField[SamplePayload]) -> None:
    assert field.to_python_value(None) is None


def test_to_python_value_already_model(field: PydanticJSONField[SamplePayload]) -> None:
    payload = SamplePayload(name="delta")
    assert field.to_python_value(payload) is payload


def test_to_db_value_serializes_model(field: PydanticJSONField[SamplePayload]) -> None:
    payload = SamplePayload(name="epsilon", count=3)
    stored = field.to_db_value(payload, Model)
    assert stored is not None
    assert json.loads(stored) == {"name": "epsilon", "count": 3}


async def test_pydantic_record_round_trip(db: None) -> None:
    record = await PydanticRecord.create(data=SamplePayload(name="stored", count=5))
    loaded = await PydanticRecord.get(id=record.id)
    assert loaded.data == SamplePayload(name="stored", count=5)
