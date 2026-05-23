# SPDX-License-Identifier: ISC
# Copyright: 2026 NiceBots.xyz
"""Minimal Tortoise models for integration tests."""

from pydantic import BaseModel
from tortoise import fields
from tortoise.models import Model
from uuid6 import UUID

from tortoise_extensions.pydantic import PydanticJSONField
from tortoise_extensions.uuid6 import FutureUUIDField


class SamplePayload(BaseModel):
    name: str
    count: int = 0


class PydanticRecord(Model):
    id = fields.IntField(primary_key=True)
    data: PydanticJSONField[SamplePayload] = PydanticJSONField(SamplePayload, default=SamplePayload)  # pyright: ignore[reportAssignmentType, reportUnknownVariableType]

    class Meta:
        table = "pydantic_records"


class UuidRecord(Model):
    id: FutureUUIDField = FutureUUIDField(primary_key=True)  # pyright: ignore[reportAssignmentType, reportUnknownVariableType]

    class Meta:
        table = "uuid_records"


__all__ = ["UUID", "PydanticRecord", "SamplePayload", "UuidRecord"]
