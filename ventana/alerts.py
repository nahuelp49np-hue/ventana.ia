from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime
from typing import Any
from zoneinfo import ZoneInfo

import httpx

from ventana import db
from ventana.config import TZ_NAME
from ventana.risk import annotate, LABELS


def _tz() -> ZoneInfo:
    settings = db.get_settings()
    name = settings.get("timezone") or TZ_NAME
    try:
        return ZoneInfo(name)
    except Exception:
        return ZoneInfo("America/Argentina/Buenos_Aires")


def _today() -> date:
    return datetime.now(_tz()).date()


def telegram_config() -> dict[str, str]:
    s = db.get_settings()
    return {
        "enabled": s.get("telegram_enabled", "0"),
        "token": (s.get("telegram_bot_token") or "").strip(),
        "chat_id": (s.get("telegram_chat_id") or "").strip(),
    }


def send_telegram(text: str) -> tuple[bool, str]:
    cfg = telegram_config()
    if not cfg["token"] or not cfg["chat_id"]:
        return False, "Telegram no está configurado."
    url = f"https://api.telegram.org/bot{cfg['token']}/sendMessage"
    try:
        r = httpx.post(
            url,
            json={
                "chat_id": cfg["chat_id"],
                "text": text,
                "disable_web_page_preview": True,
            },
            timeout=20.0,
        )
        if r.status_code >= 300:
            return False, f"Telegram {r.status_code}: {r.text[:240]}"
        return True, "ok"
    except Exception as exc:
        return False, str(exc)


def format_signal(level: str, batches: list[dict[str, Any]], title: str | None = None) -> str:
    head = title or f"SYS.VENTANA  ·  SEÑAL {LABELS.get(level, level).upper()}"
    lines = [head, ""]
    if not batches:
        lines.append("Sin lotes en esta ventana.")
        return "\n".join(lines)
    lines.append(f"{len(batches)} lote(s).")
    lines.append("")
    for i, b in enumerate(batches[:12], start=1):
        idx = f"{i:02d}"
        qty = _qty(b.get("quantity_current"), b.get("unit"))
        exp = _fmt_date(b.get("expires_at"))
        lines.append(f"{idx}  {b.get('display_name')}")
        lines.append(f"    vence {exp}  ·  {qty}  ·  {b.get('window_label')}")
        lines.append("")
    if len(batches) > 12:
        lines.append(f"… y {len(batches) - 12} más en control.")
    lines.append("VENTANA://CONTROL")
    return "\n".join(lines).strip()


def _qty(value: Any, unit: Any) -> str:
    try:
        n = float(value)
    except (TypeError, ValueError):
        return "—"
    if n == int(n):
        n_s = str(int(n))
    else:
        n_s = f"{n:.2f}".replace(".", ",")
    return f"{n_s} {unit or 'un'}"


def _fmt_date(value: Any) -> str:
    if not value:
        return "—"
    text = str(value)[:10]
    parts = text.split("-")
    if len(parts) == 3:
        return f"{parts[2]}.{parts[1]}"
    return text


def live_batches() -> list[dict[str, Any]]:
    th = db.thresholds()
    today = _today()
    rows = db.list_batches(status_in=("activo", "promocion"))
    return [annotate(r, th, today) for r in rows]


def group_by_level(batches: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for b in batches:
        grouped[b["level"]].append(b)
    return grouped


def dispatch(immediate_only: bool = False) -> dict[str, Any]:
    """Evalúa lotes y manda señales. immediate_only = solo vencido/crítico."""
    cfg = telegram_config()
    if cfg["enabled"] != "1":
        return {"skipped": True, "reason": "alertas desactivadas"}
    if not cfg["token"] or not cfg["chat_id"]:
        return {"skipped": True, "reason": "telegram incompleto"}

    batches = live_batches()
    grouped = group_by_level(batches)
    today = _today().isoformat()
    sent = []

    urgent_levels = ("vencido", "critico")
    digest_levels = ("vencido", "critico", "advertencia")
    settings = db.get_settings()
    if settings.get("digest_include_preventivo") == "1":
        digest_levels = digest_levels + ("preventivo",)

    levels = urgent_levels if immediate_only else digest_levels

    for level in levels:
        candidates = []
        for b in grouped.get(level, []):
            if db.already_alerted_today(b["id"], level, today):
                continue
            candidates.append(b)
        if not candidates:
            continue
        if immediate_only and level not in urgent_levels:
            continue
        text = format_signal(level, candidates)
        ok, detail = send_telegram(text)
        status = "enviado" if ok else "error"
        for b in candidates:
            db.log_alert(b["id"], level, "telegram", text if ok else detail, status)
        sent.append({"level": level, "count": len(candidates), "ok": ok, "detail": detail})

    return {"skipped": False, "sent": sent}


def maybe_daily_digest() -> dict[str, Any] | None:
    settings = db.get_settings()
    hour = (settings.get("alert_hour") or "08:00").strip()
    now = datetime.now(_tz())
    try:
        hh, mm = hour.split(":")
        target_h, target_m = int(hh), int(mm)
    except Exception:
        target_h, target_m = 8, 0
    # fire during the target minute
    if now.hour != target_h or now.minute != target_m:
        return None
    return dispatch(immediate_only=False)
