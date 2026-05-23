<!--
SPDX-License-Identifier: ISC
Copyright: 2026 NiceBots.xyz
-->
# Usage

Install the base package plus the extras you need:

```bash
pip install tortoise-extensions[pydantic]
pip install tortoise-extensions[uuid6]
pip install tortoise-extensions[pydantic,uuid6]
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
