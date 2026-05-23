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
pip install tortoise-extensions[pydantic,uuid6]
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
