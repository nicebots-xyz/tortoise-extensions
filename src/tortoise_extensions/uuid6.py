# SPDX-License-Identifier: ISC
# Copyright: 2026 NiceBots.xyz
"""UUID v6+ field for Tortoise ORM (via the ``uuid6`` package)."""

from typing import Any, override

from tortoise import fields
from tortoise.models import Model
from uuid6 import UUID, uuid7


class FutureUUIDField(fields.Field[UUID], UUID):  # pyright: ignore[reportUnsafeMultipleInheritance]
    """UUID field compatible with UUID v6+ and the ``uuid6`` package.

    Stores UUIDs as ``CHAR(36)`` on most backends and as native ``UUID`` on
    PostgreSQL. When used as a primary key without an explicit ``default``,
    assigns UUID7 via ``uuid6.uuid7``.

    Examples:
        >>> class Item(Model):
        ...     id: FutureUUIDField = FutureUUIDField(primary_key=True)
        ...     class Meta:
        ...         table = "items"
    """

    SQL_TYPE = "CHAR(36)"

    class _db_postgres:
        SQL_TYPE = "UUID"

    def __init__(self, **kwargs: Any) -> None:  # pyright: ignore[reportExplicitAny]
        """Initialize the field.

        Args:
            **kwargs: Tortoise field options. Primary keys without ``default``
                receive ``uuid7`` automatically.
        """
        if kwargs.pop("pk", False):
            kwargs["primary_key"] = True
        if kwargs.get("primary_key") and "default" not in kwargs:
            kwargs["default"] = uuid7
        super().__init__(**kwargs)

    @override
    def to_db_value(self, value: Any, instance: type[Model] | Model) -> str | None:  # pyright: ignore[reportExplicitAny]
        """Convert a UUID to its string database representation.

        Args:
            value: UUID value or other supported input.
            instance: Tortoise model class or instance (unused).

        Returns:
            String UUID, or ``None`` when the value is falsy.
        """
        return value and str(value)

    @override
    def to_python_value(self, value: Any) -> UUID | None:  # pyright: ignore[reportExplicitAny]
        """Convert a database value to a ``uuid6.UUID`` instance.

        Args:
            value: Raw value from the database driver.

        Returns:
            Parsed UUID, or ``None`` when the value is null.
        """
        if value is None:
            return None
        if isinstance(value, UUID):
            return value
        return UUID(str(value))


__all__ = ["FutureUUIDField"]
