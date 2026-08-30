"""App configs, validation and scripts to be run at startup."""

import logging
import logging.config
import os
import tempfile
from pathlib import Path

from alembic import command
from alembic.config import Config
from dataclasses import dataclass
from platformdirs import user_data_dir

import piirakka
from piirakka.__version__ import __version__
from piirakka.services.argparser import parser


@dataclass(frozen=True)
class _APP_CONFIG:
    # flags from command line
    _args, _ = parser.parse_known_args()
    NO_MPV: bool = _args.no_mpv
    NO_BLUETOOTH: bool = _args.no_bluetooth

    # basic stuff
    APP_VERSION: str = __version__
    APP_NAME: str = "piirakka"
    APP_AUTHOR: str = "santerj"
    BASE_DIR: Path = Path(__file__).resolve().parent  # dir of main.py

    # database stuff
    DB_NAME: str = "piirakka.db"  # file without path
    DB_DIR: str = user_data_dir(APP_NAME, APP_AUTHOR)  # path to base directory for db
    DB_PATH: Path = os.path.join(DB_DIR, DB_NAME)  # full path including file
    DB_URL: str = f"sqlite:///{DB_PATH}"

    # unix socket stuff
    MPV_SOCKET: str = os.getenv("MPV_SOCKET") or os.path.join(tempfile.gettempdir(), f"piirakka_{os.getpid()}.sock")

    def validate(self):
        """Check against forbidden combinations."""
        if self.NO_MPV and os.getenv("MPV_SOCKET", None) is None:
            # ensure that custom socket is used
            raise ValueError("MPV_SOCKET must be set when using --no-mpv")

    def __post_init__(self):
        self.validate()
        os.makedirs(self.DB_DIR, exist_ok=True)


APP_CONFIG = _APP_CONFIG()


def get_alembic_config():
    alembic_ini = os.path.join(os.path.dirname(piirakka.__file__), "migrations", "alembic.ini")

    cfg = Config(alembic_ini)

    # Point Alembic to the installed migrations
    cfg.set_main_option("script_location", os.path.join(os.path.dirname(piirakka.__file__), "migrations"))

    # IMPORTANT: override the DB path
    cfg.set_main_option("sqlalchemy.url", f"{APP_CONFIG.DB_URL}")

    return cfg


def run_migrations():
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
