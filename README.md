# Duly Backend
This repository is the backend of the Duly app. It runs on Flask.

## Getting Started
Package installation and version control is handled with Poetry. To install dependencies and enter the virtual environment
```bash
poetry install
eval $(poetry env activate)
```

To get started locally, just run
```bash
flask --app src.app.py --debug run
```

## CI
Continuous integration on GitHub actions can be mimicked locally with `tox`. Install `tox` with `pipx`

```bash
pipx install tox
```

then from the root of the project run
```bash
tox
```

If tests related to linting or formatting are failing, it is recommended to use the associated tools. Therefore, install `black`, `isort`, `iflake`, `autoflake`, `mypy` with `pipx` and use them accordingly.

## Migrations
We use Alembic out-of-the-box (not Flask-Migrate) for migrations. The important commands to keep in mind

```bash
alembic upgrade head
alembic revision --autogenerate -m "message"
alembic upgrade +1/-1
alembic history
alembic current
```

Once generated, new revisions can be manually edited in /migrations/versions. Care must be taken for upgrades and rollbacks to be reversible (although this is not always possible).

These commands should be used to upgrade or downgrade the database and used with care, since the dev database itself is not under version control. Also, alembic tracks the current revision via an `alembic_version` table in postgres.