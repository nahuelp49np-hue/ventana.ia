from __future__ import annotations

from datetime import date, datetime
from typing import Any

# Sentinel persistido: el producto no tiene ventana de vencimiento.
NO_EXPIRY = "9999-12-31"

LEVELS = (
    "vencido",
    "critico",
    "advertencia",
    "preventivo",
    "estable",
)

LABELS = {
    "vencido": "VENCIDO",
    "critico": "CRÍTICO",
    "advertencia": "ADVERTENCIA",
    "preventivo": "PREVENTIVO",
    "estable": "ESTABLE",
    "sin_vence": "NO VENCE",
    "promocion": "EN PROMOCIÓN",
    "retirado": "RETIRADO",
    "agotado": "AGOTADO",
    "activo": "ACTIVO",
}

STATUS_LABELS = {
    "activo": "ACTIVO",
    "promocion": "EN PROMOCIÓN",
    "retirado": "RETIRADO",
    "agotado": "AGOTADO",
}


def is_non_expiring(value: str | date | None) -> bool:
    if value is None or value == "":
        return False
    return str(value)[:10] == NO_EXPIRY


def parse_date(value: str | date | None) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    text = str(value)[:10]
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def days_left(expires_at: str | date | None, today: date | None = None) -> int | None:
    if is_non_expiring(expires_at):
        return None
    exp = parse_date(expires_at)
    if not exp:
        return None
    today = today or date.today()
    return (exp - today).days


def classify(days: int | None, thresholds: dict[str, int]) -> str:
    if days is None:
        return "estable"
    if days < 0:
        return "vencido"
    if days <= int(thresholds.get("critico", 2)):
        return "critico"
    if days <= int(thresholds.get("advertencia", 7)):
        return "advertencia"
    if days <= int(thresholds.get("preventivo", 15)):
        return "preventivo"
    return "estable"


def window_label(days: int | None, *, no_vence: bool = False) -> str:
    if no_vence:
        return "no vence"
    if days is None:
        return "—"
    if days < 0:
        n = abs(days)
        return f"{n}d vencido" if n != 1 else "1d vencido"
    if days == 0:
        return "hoy"
    if days == 1:
        return "1 día"
    return f"{days} días"


def annotate(batch: dict[str, Any], thresholds: dict[str, int], today: date | None = None) -> dict[str, Any]:
    row = dict(batch)
    no_vence = is_non_expiring(row.get("expires_at"))
    row["no_vence"] = no_vence
    if no_vence:
        row["days_left"] = None
        row["level"] = "sin_vence"
        row["level_label"] = LABELS["sin_vence"]
        row["window_label"] = window_label(None, no_vence=True)
        row["status_label"] = STATUS_LABELS.get(row.get("status", ""), row.get("status", ""))
        return row
    days = days_left(row.get("expires_at"), today)
    row["days_left"] = days
    row["level"] = classify(days, thresholds)
    row["level_label"] = LABELS[row["level"]]
    row["window_label"] = window_label(days)
    row["status_label"] = STATUS_LABELS.get(row.get("status", ""), row.get("status", ""))
    return row
