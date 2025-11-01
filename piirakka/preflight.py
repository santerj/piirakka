import os
import tempfile

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent   # dir of main.py
DB_NAME = "piirakka.db"
DB_PATH = BASE_DIR / f"{DB_NAME}"
DB_URL = f"sqlite:///{DB_PATH}"

def generate_socket_path():
    return os.path.join(tempfile.gettempdir(), f"piirakka_{os.getpid()}.sock")
