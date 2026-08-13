from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

DATA_DIR = ROOT / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
DB_PATH = DATA_DIR / "ventana.db"
SCHEMA_PATH = ROOT / "schema.sql"

DATA_DIR.mkdir(exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

SECRET_KEY = os.getenv("SECRET_KEY", "dev-ventana-no-usar-en-produccion")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip() or "gemini-2.5-flash"

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "5202"))
TZ_NAME = os.getenv("TZ", "America/Argentina/Buenos_Aires")

ENV_TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
ENV_TELEGRAM_CHAT = os.getenv("TELEGRAM_CHAT_ID", "").strip()

STORE_NAME = "Súper Vivar"
SYSTEM_CODE = "SYS.VENTANA"
SYSTEM_INDEX = "02"
APP_NAME = "ventana.ia"

DEFAULT_THRESHOLDS = {
    "critico": 2,
    "advertencia": 7,
    "preventivo": 15,
}

MAX_UPLOAD_BYTES = 12 * 1024 * 1024
ALLOWED_IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif"}
