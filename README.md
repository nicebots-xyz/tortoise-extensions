<!--
SPDX-License-Identifier: ISC
Copyright: 2026 NiceBots.xyz
-->
# tortoise-extensions

Optional extension field types for [Tortoise ORM](https://tortoise.github.io/). This package targets **Tortoise ORM 0.25.4 and later, but before 1.0** — Tortoise 1.x is not supported yet.

## Install

Base package (requires Tortoise ORM in the supported range):

```bash
pip install tortoise-extensions
```

Optional extras:

```bash
pip install tortoise-extensions[pydantic]
pip install tortoise-extensions[uuid6]
pip install tortoise-extensions[s3]
pip install tortoise-extensions[pydantic,uuid6,s3]
```

## Usage

### Pydantic JSON (`pydantic` extra)

```python
from pydantic import BaseModel
from tortoise.models import Model

from tortoise_extensions.pydantic import PydanticJSONField


class Settings(BaseModel):
    theme: str = "dark"


class AppConfig(Model):
    settings: PydanticJSONField[Settings] = PydanticJSONField(
        Settings, default=Settings
    )

    class Meta:
        table = "app_configs"
```

`PydanticJSONField` round-trips through your Pydantic model: it accepts dicts from PostgreSQL JSONB, JSON strings from SQLite, and serializes models with `model_dump(mode="json")` on save.

### UUID v6+ (`uuid6` extra)

```python
from tortoise.models import Model

from tortoise_extensions.uuid6 import FutureUUIDField


class Item(Model):
    id: FutureUUIDField = FutureUUIDField(primary_key=True)

    class Meta:
        table = "items"
```

Primary keys without an explicit `default` receive a UUID7 from the [`uuid6`](https://pypi.org/project/uuid6/) package. PostgreSQL uses the native `UUID` column type; other backends store `CHAR(36)`.

### S3 objects (`s3` extra)

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

The column stores the object key (`VARCHAR(1024)`); values load as `S3Object` handles backed by [`obstore`](https://pypi.org/project/obstore/). A field uses its `storage` override, otherwise the storage named after the model's Tortoise app. `ssl` picks `https` or plain `http` per storage.

`NULL` columns and new records load as empty handles that can still be written to. Writing to an empty handle generates a key, so save the model afterwards.

| Member | Behavior |
|--------|----------|
| `is_empty` | No key stored |
| `read()` | Content, or `None` when empty |
| `write(data, key=None)` | Uploads, returns the key |
| `delete()` | Removes the object and empties the handle |
| `exists()` | Whether the object is present in the storage |
| `read_or(default)` | Content, or `default` without writing |
| `get_or_write(value)` | Content, writing `value` (bytes or async factory) when empty or missing |

## Contributing a new extension

1. **Open an issue first** — describe the field behavior, SQL types per backend, which Tortoise versions you need, and the proposed optional-extra name (e.g. `pip install tortoise-extensions[myextra]`).
2. After maintainers agree on the design, open a PR that includes:
   - Implementation in `src/tortoise_extensions/<module>.py`
   - Tests under `tests/`
   - An entry in `[project.optional-dependencies]` if the field needs third-party packages
   - README and docs updates for the new field
   - ISC SPDX headers on new files (`licensor-config.yaml` applies)
3. Run `pdm run quality` locally before pushing.

## Documentation

Published at [docs.nicebots.xyz/tortoise-extensions](https://docs.nicebots.xyz/tortoise-extensions/).

```bash
pdm install -G docs
pdm run docs:build
pdm run docs:preview
pdm run docs:dev
```

## Development

```bash
pdm install -G dev -G test -G docs
pdm run quality
```

Public APIs use [Google-style docstrings](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings); `ruff` enforces this via `convention = "google"`.

## License

ISC.
