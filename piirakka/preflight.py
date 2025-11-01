from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_NAME = "piirakka.db"
DB_PATH = BASE_DIR / f"{DB_NAME}"
DATABASE_URL = f"sqlite:///{DB_PATH}"
