from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Iterable

from ventana.config import DB_PATH, DEFAULT_THRESHOLDS, ENV_TELEGRAM_CHAT, ENV_TELEGRAM_TOKEN, SCHEMA_PATH, TZ_NAME


def now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


@contextmanager
def cursor():
    conn = connect()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def _rows(result: Iterable[sqlite3.Row]) -> list[dict[str, Any]]:
    return [dict(r) for r in result]


def reset_operational_data() -> dict[str, int]:
    """Cero lotes, productos, ingresos, historial. Conserva users y settings."""
    tables = (
        "alert_log",
        "actions",
        "batches",
        "intake_lines",
        "intakes",
        "products",
    )
    before: dict[str, int] = {}
    with cursor() as conn:
        for table in tables:
            before[table] = int(conn.execute(f"SELECT COUNT(*) AS n FROM {table}").fetchone()["n"])
        conn.execute("PRAGMA foreign_keys = OFF")
        for table in tables:
            conn.execute(f"DELETE FROM {table}")
        conn.execute(
            "DELETE FROM sqlite_sequence WHERE name IN ({})".format(
                ",".join("?" * len(tables))
            ),
            tables,
        )
        conn.execute("PRAGMA foreign_keys = ON")
    vac = connect()
    try:
        vac.execute("VACUUM")
    finally:
        vac.close()
    return before


def init_db() -> None:
    schema = SCHEMA_PATH.read_text(encoding="utf-8")
    with cursor() as conn:
        conn.executescript(schema)
        _ensure_settings(conn)


def _ensure_settings(conn: sqlite3.Connection) -> None:
    defaults = {
        "store_name": "Súper Vivar",
        "threshold_critico": str(DEFAULT_THRESHOLDS["critico"]),
        "threshold_advertencia": str(DEFAULT_THRESHOLDS["advertencia"]),
        "threshold_preventivo": str(DEFAULT_THRESHOLDS["preventivo"]),
        "telegram_enabled": "0",
        "telegram_bot_token": ENV_TELEGRAM_TOKEN,
        "telegram_chat_id": ENV_TELEGRAM_CHAT,
        "alert_hour": "08:00",
        "timezone": TZ_NAME,
        "digest_include_preventivo": "0",
    }
    for key, value in defaults.items():
        conn.execute(
            "INSERT OR IGNORE INTO settings(key, value) VALUES (?, ?)",
            (key, value),
        )
    # Env tokens win on first boot if the stored value is still empty.
    if ENV_TELEGRAM_TOKEN:
        row = conn.execute(
            "SELECT value FROM settings WHERE key = 'telegram_bot_token'"
        ).fetchone()
        if row and not (row["value"] or "").strip():
            conn.execute(
                "UPDATE settings SET value = ? WHERE key = 'telegram_bot_token'",
                (ENV_TELEGRAM_TOKEN,),
            )
    if ENV_TELEGRAM_CHAT:
        row = conn.execute(
            "SELECT value FROM settings WHERE key = 'telegram_chat_id'"
        ).fetchone()
        if row and not (row["value"] or "").strip():
            conn.execute(
                "UPDATE settings SET value = ? WHERE key = 'telegram_chat_id'",
                (ENV_TELEGRAM_CHAT,),
            )


def get_setting(key: str, default: str = "") -> str:
    with cursor() as conn:
        row = conn.execute(
            "SELECT value FROM settings WHERE key = ?", (key,)
        ).fetchone()
    return row["value"] if row else default


def get_settings() -> dict[str, str]:
    with cursor() as conn:
        rows = conn.execute("SELECT key, value FROM settings").fetchall()
    return {r["key"]: r["value"] for r in rows}


def set_settings(values: dict[str, str]) -> None:
    with cursor() as conn:
        for key, value in values.items():
            conn.execute(
                "INSERT INTO settings(key, value) VALUES (?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (key, value),
            )


def thresholds() -> dict[str, int]:
    s = get_settings()
    return {
        "critico": int(s.get("threshold_critico") or DEFAULT_THRESHOLDS["critico"]),
        "advertencia": int(s.get("threshold_advertencia") or DEFAULT_THRESHOLDS["advertencia"]),
        "preventivo": int(s.get("threshold_preventivo") or DEFAULT_THRESHOLDS["preventivo"]),
    }


# ——— users ———

def get_user_by_username(username: str) -> dict[str, Any] | None:
    with cursor() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE username = ? AND active = 1",
            (username.strip().lower(),),
        ).fetchone()
    return dict(row) if row else None


def get_user(user_id: int) -> dict[str, Any] | None:
    with cursor() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return dict(row) if row else None


def list_users() -> list[dict[str, Any]]:
    with cursor() as conn:
        rows = conn.execute(
            "SELECT id, username, role, display_name, active, created_at, last_login_at "
            "FROM users ORDER BY id"
        ).fetchall()
    return _rows(rows)


def create_user(username: str, password_hash: str, role: str, display_name: str) -> int:
    with cursor() as conn:
        cur = conn.execute(
            "INSERT INTO users(username, password_hash, role, display_name, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (username.strip().lower(), password_hash, role, display_name, now_iso()),
        )
        return int(cur.lastrowid)


def touch_login(user_id: int) -> None:
    with cursor() as conn:
        conn.execute(
            "UPDATE users SET last_login_at = ? WHERE id = ?",
            (now_iso(), user_id),
        )


def count_users() -> int:
    with cursor() as conn:
        return int(conn.execute("SELECT COUNT(*) AS n FROM users").fetchone()["n"])


# ——— products ———

def list_products(q: str = "") -> list[dict[str, Any]]:
    with cursor() as conn:
        if q.strip():
            like = f"%{q.strip()}%"
            rows = conn.execute(
                "SELECT * FROM products WHERE name LIKE ? OR IFNULL(sku,'') LIKE ? "
                "ORDER BY name COLLATE NOCASE",
                (like, like),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM products ORDER BY name COLLATE NOCASE"
            ).fetchall()
    return _rows(rows)


def get_product(product_id: int) -> dict[str, Any] | None:
    with cursor() as conn:
        row = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    return dict(row) if row else None


def upsert_product(
    name: str,
    sku: str | None,
    category: str,
    unit: str,
    default_life_days: int | None,
    notes: str = "",
    product_id: int | None = None,
) -> int:
    stamp = now_iso()
    sku_val = (sku or "").strip() or None
    with cursor() as conn:
        if product_id:
            conn.execute(
                "UPDATE products SET name=?, sku=?, category=?, unit=?, "
                "default_life_days=?, notes=?, updated_at=? WHERE id=?",
                (name.strip(), sku_val, category.strip(), unit.strip() or "un",
                 default_life_days, notes, stamp, product_id),
            )
            return product_id
        cur = conn.execute(
            "INSERT INTO products(sku, name, category, unit, default_life_days, notes, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (sku_val, name.strip(), category.strip(), unit.strip() or "un",
             default_life_days, notes, stamp, stamp),
        )
        return int(cur.lastrowid)


def find_product_by_name(name: str) -> dict[str, Any] | None:
    with cursor() as conn:
        row = conn.execute(
            "SELECT * FROM products WHERE lower(name) = lower(?)",
            (name.strip(),),
        ).fetchone()
    return dict(row) if row else None


# ——— intakes ———

def create_intake(
    *,
    photo_path: str | None,
    supplier: str,
    document_number: str,
    document_date: str | None,
    raw_ocr: str | None,
    confidence: float | None,
    warnings: list[str],
    created_by: int | None,
) -> int:
    with cursor() as conn:
        cur = conn.execute(
            "INSERT INTO intakes(photo_path, supplier, document_number, document_date, "
            "raw_ocr, confidence, status, warnings, created_by, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, 'borrador', ?, ?, ?)",
            (
                photo_path,
                supplier or "",
                document_number or "",
                document_date,
                raw_ocr,
                confidence,
                json.dumps(warnings or [], ensure_ascii=False),
                created_by,
                now_iso(),
            ),
        )
        return int(cur.lastrowid)


def add_intake_line(
    intake_id: int,
    raw_name: str,
    quantity: float,
    unit: str,
    product_id: int | None = None,
    expires_at: str | None = None,
    notes: str = "",
    sort_order: int = 0,
) -> int:
    with cursor() as conn:
        cur = conn.execute(
            "INSERT INTO intake_lines(intake_id, product_id, raw_name, quantity, unit, expires_at, notes, sort_order) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (intake_id, product_id, raw_name, quantity, unit or "un", expires_at, notes, sort_order),
        )
        return int(cur.lastrowid)


def get_intake(intake_id: int) -> dict[str, Any] | None:
    with cursor() as conn:
        row = conn.execute("SELECT * FROM intakes WHERE id = ?", (intake_id,)).fetchone()
        if not row:
            return None
        data = dict(row)
        lines = conn.execute(
            "SELECT * FROM intake_lines WHERE intake_id = ? ORDER BY sort_order, id",
            (intake_id,),
        ).fetchall()
        data["lines"] = _rows(lines)
        try:
            data["warnings"] = json.loads(data.get("warnings") or "[]")
        except json.JSONDecodeError:
            data["warnings"] = []
        return data


def update_intake_header(intake_id: int, supplier: str, document_number: str, document_date: str | None) -> None:
    with cursor() as conn:
        conn.execute(
            "UPDATE intakes SET supplier=?, document_number=?, document_date=? WHERE id=?",
            (supplier, document_number, document_date or None, intake_id),
        )


def replace_intake_lines(intake_id: int, lines: list[dict[str, Any]]) -> None:
    with cursor() as conn:
        conn.execute("DELETE FROM intake_lines WHERE intake_id = ?", (intake_id,))
        for i, line in enumerate(lines):
            conn.execute(
                "INSERT INTO intake_lines(intake_id, product_id, raw_name, quantity, unit, expires_at, notes, sort_order) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    intake_id,
                    line.get("product_id"),
                    line.get("raw_name") or "",
                    float(line.get("quantity") or 0),
                    line.get("unit") or "un",
                    line.get("expires_at") or None,
                    line.get("notes") or "",
                    i,
                ),
            )


def confirm_intake(intake_id: int) -> None:
    with cursor() as conn:
        conn.execute(
            "UPDATE intakes SET status='confirmado', confirmed_at=? WHERE id=?",
            (now_iso(), intake_id),
        )


def discard_intake(intake_id: int) -> None:
    with cursor() as conn:
        conn.execute(
            "UPDATE intakes SET status='descartado' WHERE id=?",
            (intake_id,),
        )


# ——— batches ———

def create_batch(
    *,
    product_id: int | None,
    intake_id: int | None,
    intake_line_id: int | None,
    display_name: str,
    sku: str | None,
    category: str,
    quantity: float,
    unit: str,
    received_at: str,
    expires_at: str,
    notes: str,
    created_by: int | None,
) -> int:
    stamp = now_iso()
    with cursor() as conn:
        cur = conn.execute(
            "INSERT INTO batches(product_id, intake_id, intake_line_id, display_name, sku, category, "
            "quantity_initial, quantity_current, unit, received_at, expires_at, status, notes, "
            "created_by, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'activo', ?, ?, ?, ?)",
            (
                product_id, intake_id, intake_line_id, display_name, sku, category or "",
                quantity, quantity, unit or "un", received_at, expires_at, notes or "",
                created_by, stamp, stamp,
            ),
        )
        return int(cur.lastrowid)


def list_batches(status_in: tuple[str, ...] | None = None) -> list[dict[str, Any]]:
    sql = "SELECT * FROM batches"
    params: list[Any] = []
    if status_in:
        placeholders = ",".join("?" * len(status_in))
        sql += f" WHERE status IN ({placeholders})"
        params.extend(status_in)
    sql += " ORDER BY expires_at ASC, id ASC"
    with cursor() as conn:
        rows = conn.execute(sql, params).fetchall()
    return _rows(rows)


def get_batch(batch_id: int) -> dict[str, Any] | None:
    with cursor() as conn:
        row = conn.execute("SELECT * FROM batches WHERE id = ?", (batch_id,)).fetchone()
    return dict(row) if row else None


def update_batch(
    batch_id: int,
    *,
    quantity_current: float | None = None,
    status: str | None = None,
    notes: str | None = None,
    expires_at: str | None = None,
) -> None:
    fields = ["updated_at = ?"]
    params: list[Any] = [now_iso()]
    if quantity_current is not None:
        fields.append("quantity_current = ?")
        params.append(quantity_current)
    if status is not None:
        fields.append("status = ?")
        params.append(status)
    if notes is not None:
        fields.append("notes = ?")
        params.append(notes)
    if expires_at is not None:
        fields.append("expires_at = ?")
        params.append(expires_at)
    params.append(batch_id)
    with cursor() as conn:
        conn.execute(f"UPDATE batches SET {', '.join(fields)} WHERE id = ?", params)


def log_action(
    batch_id: int | None,
    user_id: int | None,
    kind: str,
    quantity_before: float | None,
    quantity_after: float | None,
    notes: str = "",
) -> int:
    with cursor() as conn:
        cur = conn.execute(
            "INSERT INTO actions(batch_id, user_id, kind, quantity_before, quantity_after, notes, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (batch_id, user_id, kind, quantity_before, quantity_after, notes, now_iso()),
        )
        return int(cur.lastrowid)


def list_actions(limit: int = 200, kind: str | None = None) -> list[dict[str, Any]]:
    sql = (
        "SELECT a.*, b.display_name, b.unit, u.display_name AS user_name "
        "FROM actions a "
        "LEFT JOIN batches b ON b.id = a.batch_id "
        "LEFT JOIN users u ON u.id = a.user_id "
    )
    params: list[Any] = []
    if kind:
        sql += "WHERE a.kind = ? "
        params.append(kind)
    sql += "ORDER BY a.created_at DESC, a.id DESC LIMIT ?"
    params.append(limit)
    with cursor() as conn:
        rows = conn.execute(sql, params).fetchall()
    return _rows(rows)


def list_actions_for_batch(batch_id: int) -> list[dict[str, Any]]:
    with cursor() as conn:
        rows = conn.execute(
            "SELECT a.*, u.display_name AS user_name "
            "FROM actions a LEFT JOIN users u ON u.id = a.user_id "
            "WHERE a.batch_id = ? ORDER BY a.created_at DESC",
            (batch_id,),
        ).fetchall()
    return _rows(rows)


def already_alerted_today(batch_id: int, level: str, day_prefix: str) -> bool:
    with cursor() as conn:
        row = conn.execute(
            "SELECT id FROM alert_log WHERE batch_id = ? AND level = ? AND sent_at LIKE ? LIMIT 1",
            (batch_id, level, f"{day_prefix}%"),
        ).fetchone()
    return row is not None


def log_alert(batch_id: int | None, level: str, channel: str, payload: str, status: str = "enviado") -> None:
    with cursor() as conn:
        conn.execute(
            "INSERT INTO alert_log(batch_id, level, channel, payload, status, sent_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (batch_id, level, channel, payload, status, now_iso()),
        )
