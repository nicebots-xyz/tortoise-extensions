<!--
SPDX-License-Identifier: ISC
Copyright: 2026 NiceBots.xyz
-->
# Usage

Install the base package plus the extras you need:

```bash
pip install tortoise-extensions[pydantic]
pip install tortoise-extensions[uuid6]
pip install tortoise-extensions[s3]
pip install tortoise-extensions[pydantic,uuid6,s3]
```

## Pydantic JSON field

Requires the `pydantic` extra.

```python
from pydantic import BaseModel
from tortoise.models import Model

from tortoise_extensions.pydantic import PydanticJSONField


class Settings(BaseModel):
    theme: str = "dark"


class AppConfig(Model):
    settings: PydanticJSONField[Settings] = PydanticJSONField(Settings, default=Settings)

    class Meta:
        table = "app_configs"
```

`PydanticJSONField` validates JSON using your Pydantic model. It accepts dict values from PostgreSQL JSONB and JSON strings from SQLite.

## UUID v6+ field

Requires the `uuid6` extra.

```python
from tortoise.models import Model

from tortoise_extensions.uuid6 import FutureUUIDField


class Item(Model):
    id: FutureUUIDField = FutureUUIDField(primary_key=True)

    class Meta:
        table = "items"
```

Primary keys without an explicit `default` are assigned UUID7. PostgreSQL uses the native `UUID` column type; other backends use `CHAR(36)`.

## S3 field

Requires the `s3` extra.

```python
from tortoise.models import Model

from tortoise_extensions.s3 import S3Field, S3Storage, init_storages


class Attachment(Model):
    file = S3Field(null=True)
    thumb = S3Field(storage="cdn", null=True)


init_storages({
    "models": S3Storage(endpoint="s3.example.com", bucket="main", access_key="...", secret_key="..."),
    "cdn": S3Storage(endpoint="minio:9000", bucket="cdn", access_key="...", secret_key="...", ssl=False),
})

record = await Attachment.create()
await record.file.write(b"hello")
await record.save()

data = await record.file.read()
thumb = await record.thumb.get_or_write(render_thumbnail)
await record.save()
```

The column stores the object key (`VARCHAR(1024)`) and loads as an `S3Object` handle backed by [`obstore`](https://pypi.org/project/obstore/).

| Setting | Effect |
|---------|--------|
| `S3Storage.endpoint` | Host and optional port, without scheme |
| `S3Storage.bucket` | Bucket holding the objects |
| `S3Storage.access_key` / `secret_key` | Credentials |
| `S3Storage.region` | Signing region, resolved by `obstore` when omitted |
| `S3Storage.ssl` | `https` when `True` (default), plain `http` when `False` |
| `S3Field(storage=...)` | Storage name, defaults to the model's Tortoise app |
