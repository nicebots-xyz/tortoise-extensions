<!--
SPDX-License-Identifier: ISC
Copyright: 2026 NiceBots.xyz
-->
# tortoise-extensions

`tortoise-extensions` provides optional Tortoise ORM field types as install extras.

Supported Tortoise ORM versions: **0.25.4 and later, but before 1.0**. Tortoise 1.x is not supported yet.

## Install

```bash
pip install tortoise-extensions[pydantic,uuid6]
```

See [Usage](usage.md) for field-specific setup.

## Quick example

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
