import logging
import logging.config
import os
import tempfile

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent   # dir of main.py
DB_NAME = "piirakka.db"
DB_PATH = BASE_DIR / f"{DB_NAME}"
DB_URL = f"sqlite:///{DB_PATH}"

def generate_socket_path():
    return os.path.join(tempfile.gettempdir(), f"piirakka_{os.getpid()}.sock")

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
        "alembic": {
            "level": "INFO",
            "handlers": ["console"],
            "propagate": False,
        },
    },
}

logging.config.dictConfig(LOGGING_CONFIG)
