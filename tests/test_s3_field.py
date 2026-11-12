# SPDX-License-Identifier: ISC
# Copyright: 2026 NiceBots.xyz

import pytest
from obstore.store import MemoryStore, S3Store
from tortoise.exceptions import ConfigurationError
from tortoise.models import Model

from tests.models import S3Record
from tortoise_extensions.s3 import S3Field, S3Object, S3Storage, get_store, init_storages


def _storage(*, ssl: bool) -> S3Storage:
    return S3Storage(endpoint="localhost:9000", bucket="bucket", access_key="key", secret_key="secret", ssl=ssl)


@pytest.mark.parametrize(("ssl", "scheme"), [(True, "https"), (False, "http")])
def test_storage_ssl_toggle(ssl: bool, scheme: str) -> None:
    init_storages({"models": _storage(ssl=ssl)})
    store = get_store("models")
    assert isinstance(store, S3Store)
    assert store.config.get("endpoint") == f"{scheme}://localhost:9000"
    assert str((store.client_options or {}).get("allow_http")).lower() == str(not ssl).lower()


def test_storage_rejects_scheme() -> None:
    with pytest.raises(ValueError, match="scheme"):
        S3Storage(endpoint="http://localhost:9000", bucket="b", access_key="k", secret_key="s")


def test_unknown_storage() -> None:
    init_storages({})
    with pytest.raises(ConfigurationError, match="missing"):
        get_store("missing")


def test_db_value_conversion() -> None:
    field = S3Field(storage="other")
    assert field.to_db_value(S3Object("other", "a/b"), Model) == "a/b"
    assert field.to_db_value(S3Object("other"), Model) is None
    assert field.to_db_value("raw", Model) == "raw"
    assert field.to_db_value(None, Model) is None


def test_python_value_conversion() -> None:
    field = S3Field(storage="other")
    handle = S3Object("other", "k")
    assert field.to_python_value(handle) is handle
    assert field.to_python_value("k") == handle
    assert field.to_python_value(None) == S3Object("other")


async def test_storage_resolution(db: None, stores: dict[str, MemoryStore]) -> None:
    record = await S3Record.create()
    assert record.file == S3Object("models")
    assert record.other == S3Object("other")

    key = await record.file.write(b"main")
    assert await stores["models"].head_async(key)
    assert not await S3Object("other", key).exists()


async def test_round_trip_nullable(db: None, stores: dict[str, MemoryStore]) -> None:
    record = await S3Record.create()
    assert record.file.is_empty
    assert await record.file.read() is None

    await record.file.write(b"hello")
    await record.save()

    loaded = await S3Record.get(id=record.id)
    assert not loaded.file.is_empty
    assert await loaded.file.read() == b"hello"
    assert loaded.other.is_empty

    await loaded.file.delete()
    assert loaded.file.is_empty
    await loaded.save()

    reloaded = await S3Record.get(id=record.id)
    assert reloaded.file == S3Object("models")
    await reloaded.file.delete()


async def test_write_explicit_key(db: None, stores: dict[str, MemoryStore]) -> None:
    record = await S3Record.create()
    assert await record.file.write(b"x", key="avatars/1.png") == "avatars/1.png"
    await record.save()
    assert await S3Record.filter(file="avatars/1.png").count() == 1


async def test_exists(db: None, stores: dict[str, MemoryStore]) -> None:
    assert not await S3Object("models").exists()
    assert not await S3Object("models", "dangling").exists()
    handle = S3Object("models")
    await handle.write(b"x")
    assert await handle.exists()


async def test_read_or(db: None, stores: dict[str, MemoryStore]) -> None:
    empty = S3Object("models")
    assert await empty.read_or(b"fallback") == b"fallback"
    assert empty.is_empty
    assert await S3Object("models", "dangling").read_or(b"fallback") == b"fallback"


async def test_get_or_write(db: None, stores: dict[str, MemoryStore]) -> None:
    calls = 0

    async def factory() -> bytes:
        nonlocal calls
        calls += 1
        return b"rendered"

    handle = S3Object("models")
    assert await handle.get_or_write(factory) == b"rendered"
    assert await handle.get_or_write(factory) == b"rendered"
    assert calls == 1

    dangling = S3Object("models", "dangling")
    assert await dangling.get_or_write(b"repaired") == b"repaired"
    assert dangling.key == "dangling"
    assert await dangling.read() == b"repaired"
