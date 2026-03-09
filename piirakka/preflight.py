import logging
import logging.config
import os
import tempfile
from pathlib import Path

from alembic import command
from alembic.config import Config
from platformdirs import user_data_dir

import piirakka

APP_NAME = "piirakka"
APP_AUTHOR = "santerj"

db_dir = user_data_dir(APP_NAME, APP_AUTHOR)
os.makedirs(db_dir, exist_ok=True)

DB_PATH = os.path.join(db_dir, "piirakka.db")

if override := os.getenv("PIIRAKKA_DB"):
    DB_PATH = override

BASE_DIR = Path(__file__).resolve().parent  # dir of main.py
DB_NAME = "piirakka.db"
# DB_PATH = BASE_DIR / f"{DB_NAME}"
DB_URL = f"sqlite:///{DB_PATH}"


def generate_socket_path():
    return os.path.join(tempfile.gettempdir(), f"piirakka_{os.getpid()}.sock")


def get_alembic_config():
    alembic_ini = os.path.join(os.path.dirname(piirakka.__file__), "migrations", "alembic.ini")

    cfg = Config(alembic_ini)

    # Point Alembic to the installed migrations
    cfg.set_main_option("script_location", os.path.join(os.path.dirname(piirakka.__file__), "migrations"))

    # IMPORTANT: override the DB path
    cfg.set_main_option("sqlalchemy.url", f"{DB_URL}")

    return cfg


def run_migrations():
    # Path to alembic.ini inside the installed package
    alembic_ini = os.path.join(os.path.dirname(piirakka.__file__), "migrations", "alembic.ini")

    cfg = get_alembic_config()

    # Override script_location to point to the installed package
    cfg.set_main_option("script_location", os.path.join(os.path.dirname(piirakka.__file__), "migrations"))

    command.upgrade(cfg, "head")


LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
        },
    },
    "root": {
        "level": "INFO",
        "handlers": ["console"],
    },
    "loggers": {
        "uvicorn": {
            "level": "INFO",
            "handlers": ["console"],
            "propagate": False,
        },
        "uvicorn.error": {
            "level": "INFO",
            "handlers": ["console"],
            "propagate": False,
        },
        "uvicorn.access": {
            "level": "INFO",
            "handlers": ["console"],
            "propagate": False,
        },
        "sqlalchemy": {
            "level": "INFO",
            "handlers": ["console"],
            "propagate": False,
        },
        "sqlalchemy.engine": {
            "level": "INFO",
            "handlers": ["console"],
            "propagate": False,
        },
        "sqlalchemy.orm": {
            "level": "INFO",
            "handlers": ["console"],
            "propagate": False,
        },
        "alembic": {
            "level": "INFO",
            "handlers": ["console"],
            "propagate": False,
        },
    },
}

logging.config.dictConfig(LOGGING_CONFIG)
