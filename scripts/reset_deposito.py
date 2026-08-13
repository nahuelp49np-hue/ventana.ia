"""Pone la base en cero para el depósito. Conserva usuarios y carátulas de ejemplo."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ventana import db
from ventana.config import UPLOAD_DIR
from ventana.seed import seed_if_empty


def main() -> int:
    db.init_db()
    before = db.reset_operational_data()
    seed_if_empty()
    removed = 0
    for path in UPLOAD_DIR.glob("*"):
        if path.name == ".gitkeep":
            continue
        if path.is_file():
            path.unlink()
            removed += 1
    users = db.list_users()
    print("SYS.VENTANA  ·  BASE EN CERO")
    for table, n in before.items():
        print(f"  {table}: {n} → 0")
    print(f"  uploads: {removed} archivo(s) de ingreso")
    print("  usuarios:", ", ".join(f"{u['username']}/{u['role']}" for u in users))
    print("  carátulas: 1652 Amstel · 1647 Arcor (intactas)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
