import logging

from sqlalchemy import inspect as sa_inspect

from src.adapters.orm.base import mapper_registry
from src.adapters.orm.users import user_table
from src.domain import User


def start_mappers():
    if sa_inspect(User, raiseerr=False) is not None:
        return

    try:
        mapper_registry.map_imperatively(
            User, user_table, properties={"role": user_table.c.role_id}
        )
    except Exception as e:
        logging.error(f"Error while starting mappers: {e}")
        raise
