<!--
SPDX-License-Identifier: ISC
Copyright: 2026 NiceBots.xyz
-->
# Contributing

## Proposing a new extension

1. Open an issue describing the field behavior, SQL types per backend, Tortoise version requirements, and the proposed optional-extra name.
2. Wait for maintainer feedback before starting implementation.

## Pull requests

Include:

- Implementation in `src/tortoise_extensions/<module>.py`
- Google-style docstrings on public APIs
- Tests under `tests/`
- Optional dependency entry in `pyproject.toml` when third-party packages are required
- Updates to `docs/usage.md` and `docs/api.md` when user-facing behavior changes

Run the quality gate locally:

```bash
pdm install -G dev -G test -G docs
pdm run quality
pdm run docs:build
```
