# SPDX-License-Identifier: ISC
# Copyright: 2026 NiceBots.xyz
"""Pydantic-backed JSON field for Tortoise ORM."""

from typing import Any, override

from pydantic import BaseModel
from tortoise.fields.data import JSONField
from tortoise.models import Model


class PydanticJSONField[T: BaseModel](JSONField[dict[str, object]]):
    """JSONField that round-trips values through a Pydantic model.

    On save, serializes ``BaseModel`` instances with ``model_dump(mode="json")``
    before JSON encoding. On load, validates decoded data with the configured
    Pydantic model, including:

    - JSON strings or bytes (typical for SQLite).
    - Plain dicts returned by PostgreSQL JSONB drivers such as asyncpg.

    Examples:
        >>> class MyModel(Model):
        ...     data: PydanticJSONField[MyPydanticModel] = PydanticJSONField(
        ...         MyPydanticModel, default=MyPydanticModel
        ...     )
    """

    def __init__(self, model_class: type[T], **kwargs: Any) -> None:
        """Initialize the field.

        Args:
            model_class: Pydantic model class used for validation.
            **kwargs: Additional arguments forwarded to ``JSONField``.
        """
        self._pydantic_model: type[T] = model_class
        super().__init__(**kwargs)

    @override
    def to_python_value(self, value: Any) -> T | None:  # pyright: ignore[reportExplicitAny, reportIncompatibleMethodOverride]
        """Convert a database value to a Pydantic model instance.

        Args:
            value: Raw value from the database driver.

        Returns:
            A validated Pydantic model, or ``None`` when the value is null.
        """
        if value is None:
            return None
        if isinstance(value, self._pydantic_model):
            return value
        if isinstance(value, (str, bytes)):
            raw = value if isinstance(value, str) else value.decode()
            return self._pydantic_model.model_validate_json(raw)
        return self._pydantic_model.model_validate(value)

    @override
    def to_db_value(self, value: Any, instance: type[Model] | Model) -> str | None:  # pyright: ignore[reportExplicitAny]
        """Convert a Python value to a JSON string for storage.

        Args:
            value: Model instance or JSON-serializable data.
            instance: Tortoise model class or instance (unused).

        Returns:
            Encoded JSON string, or ``None`` when the value is null.
        """
        if isinstance(value, BaseModel):
            value = value.model_dump(mode="json")
        return super().to_db_value(value, instance)


__all__ = ["PydanticJSONField"]
