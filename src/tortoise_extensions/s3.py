# SPDX-License-Identifier: ISC
# Copyright: 2026 NiceBots.xyz
"""S3-backed field for Tortoise ORM (via the ``obstore`` package)."""

import sys
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, override

from obstore.store import ObjectStore, S3Store
from tortoise import fields
from tortoise.exceptions import ConfigurationError
from tortoise.models import Model

if sys.version_info >= (3, 14):
    from uuid import uuid7
else:
    from uuid6 import uuid7

if TYPE_CHECKING:
    from obstore.store import S3Config

_stores: dict[str, ObjectStore] = {}


@dataclass(frozen=True, slots=True, kw_only=True)
class S3Storage:
    """Connection settings for one S3-compatible endpoint.

    Attributes:
        endpoint: Host and optional port, without scheme (e.g. ``"minio:9000"``).
        bucket: Bucket holding the objects.
        access_key: Access key ID.
        secret_key: Secret access key.
        region: Signing region, or ``None`` to let ``obstore`` resolve it (``AWS_REGION``, else ``us-east-1``).
        ssl: Use ``https`` when ``True``, plain ``http`` when ``False``.
    """

    endpoint: str
    bucket: str
    access_key: str
    secret_key: str
    region: str | None = None
    ssl: bool = True

    def __post_init__(self) -> None:
        """Validate the endpoint.

        Raises:
            ValueError: If the endpoint contains a scheme, which ``ssl`` controls.
        """
        if "://" in self.endpoint:
            raise ValueError("S3Storage.endpoint must not contain a scheme, use `ssl` instead")

    def to_store(self) -> S3Store:
        """Build the ``obstore`` store for these settings.

        Returns:
            A configured ``S3Store``.
        """
        config: S3Config = {
            "endpoint": f"{'https' if self.ssl else 'http'}://{self.endpoint}",
            "access_key_id": self.access_key,
            "secret_access_key": self.secret_key,
        }
        if self.region is not None:
            config["region"] = self.region
        return S3Store(self.bucket, config=config, client_options={"allow_http": not self.ssl})


def init_storages(storages: Mapping[str, S3Storage | ObjectStore]) -> None:
    """Register the named storages used by ``S3Field``, replacing any previous ones.

    Names are Tortoise app labels (the default storage of every model in that app)
    or free names referenced through ``S3Field(storage=...)``.

    Args:
        storages: Storage settings, or ready ``obstore`` stores, by name.
    """
    _stores.clear()
    _stores.update(
        {name: value.to_store() if isinstance(value, S3Storage) else value for name, value in storages.items()}
    )


def get_store(name: str) -> ObjectStore:
    """Return a registered store.

    Args:
        name: Storage name.

    Returns:
        The registered store.

    Raises:
        ConfigurationError: If no storage is registered under ``name``.
    """
    try:
        return _stores[name]
    except KeyError:
        raise ConfigurationError(f"S3 storage {name!r} is not initialized, see `init_storages`") from None


@dataclass(slots=True)
class S3Object:
    """Handle on an object stored in S3, as loaded from an ``S3Field``.

    An empty handle (``key is None``) maps to ``NULL`` and can still be written to.
    Writing to an empty handle generates a key, so the model must be saved afterwards.

    Attributes:
        storage: Name of the storage holding the object.
        key: Object key, or ``None`` when nothing is stored.
    """

    storage: str
    key: str | None = None

    @property
    def is_empty(self) -> bool:
        """Whether the handle has no key (no I/O performed)."""
        return self.key is None

    async def read(self) -> bytes | None:
        """Download the object.

        Returns:
            The object content, or ``None`` when the handle is empty.
        """
        if self.key is None:
            return None
        result = await get_store(self.storage).get_async(self.key)
        return bytes(await result.bytes_async())

    async def write(self, data: bytes, *, key: str | None = None) -> str:
        """Upload ``data``, generating a UUID7 key when the handle has none.

        Args:
            data: Content to store.
            key: Explicit key to write to, replacing the current one.

        Returns:
            The key written to.
        """
        target = key or self.key or uuid7().hex
        await get_store(self.storage).put_async(target, data)
        self.key = target
        return target

    async def delete(self) -> None:
        """Delete the object and empty the handle. Does nothing when already empty."""
        if self.key is None:
            return
        await get_store(self.storage).delete_async(self.key)
        self.key = None

    async def exists(self) -> bool:
        """Check whether the object exists in the storage.

        Returns:
            ``False`` when the handle is empty or the object is missing.
        """
        if self.key is None:
            return False
        try:
            await get_store(self.storage).head_async(self.key)
        except FileNotFoundError:
            return False
        return True

    async def read_or(self, default: bytes) -> bytes:
        """Download the object, falling back to ``default`` without writing it.

        Args:
            default: Value returned when the handle is empty or the object is missing.

        Returns:
            The object content, or ``default``.
        """
        try:
            data = await self.read()
        except FileNotFoundError:
            return default
        return default if data is None else data

    async def get_or_write(self, value: bytes | Callable[[], Awaitable[bytes]]) -> bytes:
        """Download the object, writing ``value`` first when it is empty or missing.

        Args:
            value: Content to store, or an async factory only awaited when needed.

        Returns:
            The stored content.
        """
        try:
            data = await self.read()
        except FileNotFoundError:
            data = None
        if data is not None:
            return data
        data = value if isinstance(value, bytes) else await value()
        await self.write(data)
        return data


class S3Field(fields.Field[S3Object]):
    """Field storing an S3 object key, loaded as an ``S3Object`` handle.

    The storage is ``storage`` when given, otherwise the model's Tortoise app label.
    ``NULL`` columns and new instances load as empty, writable handles.

    Examples:
        >>> class Attachment(Model):
        ...     file = S3Field(null=True)
        ...     thumb = S3Field(storage="cdn", null=True)
    """

    SQL_TYPE = "VARCHAR(1024)"
    field_type = S3Object

    def __init__(self, storage: str | None = None, **kwargs: Any) -> None:  # pyright: ignore[reportExplicitAny]
        """Initialize the field.

        Args:
            storage: Storage name overriding the model's app label.
            **kwargs: Tortoise field options.
        """
        self._storage: str | None = storage
        kwargs.setdefault("default", self._empty)
        super().__init__(**kwargs)

    @property
    def storage_name(self) -> str:
        """Storage name resolved from the override or the model's app label.

        Raises:
            ConfigurationError: If neither is available (Tortoise not initialized).
        """
        if self._storage is not None:
            return self._storage
        app = self.model._meta.app if self.model else None  # noqa: SLF001 # pyright: ignore[reportPrivateUsage, reportUnnecessaryComparison]
        if app is None:
            raise ConfigurationError(f"{self.model_field_name!r} has no storage, pass one or initialize Tortoise")
        return app

    def _empty(self) -> S3Object:
        return S3Object(self.storage_name)

    @override
    def to_python_value(self, value: Any) -> S3Object:  # pyright: ignore[reportExplicitAny]
        """Convert a database value to an ``S3Object`` handle.

        Args:
            value: Stored key, handle, or ``None``.

        Returns:
            A handle, empty when the value is ``None``.
        """
        if isinstance(value, S3Object):
            return value
        return S3Object(self.storage_name, None if value is None else str(value))

    @override
    def to_db_value(self, value: Any, instance: type[Model] | Model) -> str | None:  # pyright: ignore[reportExplicitAny]
        """Convert a handle or key to its database representation.

        Args:
            value: Handle, raw key, or ``None``.
            instance: Tortoise model class or instance (unused).

        Returns:
            The object key, or ``None`` when empty.
        """
        if isinstance(value, S3Object):
            return value.key
        return None if value is None else str(value)


__all__ = ["S3Field", "S3Object", "S3Storage", "get_store", "init_storages"]
