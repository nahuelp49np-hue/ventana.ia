from __future__ import annotations

import io
import json
import re
from collections import OrderedDict
from pathlib import Path
from typing import Any

from ventana.config import GEMINI_API_KEY, GEMINI_MODEL, GEMINI_MODEL_FALLBACKS

EXTRACT_PROMPT = """Sos el lector de documentos de ventana.ia, sistema de control de vida útil de Súper Vivar (Posadas, Misiones, Argentina).

El documento más frecuente NO es un remito de proveedor. Es un papel interno del supermercado:

  «Reporte Movimientos por Caratulas»
  Logo Súper Vivar
  Fila de cabecera: número de carátula + «INGRESO LOGICOM FC: …» o «INGRESO LOGEX FC: …» + usuario + fecha
  Columnas: Fecha y Hora Proceso | Productos | Mov | Dep | Ingresos | Egresos
  Mov suele ser RSC. Dep suele ser VTA.
  Cierre: total de Ingresos y Egresos (a veces 0.00).

También pueden llegar remitos, facturas o tickets de proveedor. Detectá el tipo.

La foto es de celular en depósito: sombra de la mano, flash, recorte, teclado de fondo. Leé lo visible. No inventes lo que la sombra tapa.

Devolvé SOLO un JSON válido, sin markdown:

{
  "document_type": "caratula|remito|factura|otro",
  "source_system": "LOGICOM|LOGEX|null",
  "caratula_number": "1647 o null",
  "operator": "JoseG o null",
  "supplier": "LOGICOM, LOGEX, o el proveedor si es remito",
  "document_number": "número de FC/remito (ej. 14-712036). No pongas acá el total.",
  "document_date": "YYYY-MM-DD o null",
  "confidence": 0.0,
  "lines": [
    {
      "name": "nombre tal como está en Productos, sin la fecha/hora de la izquierda",
      "quantity": 0,
      "unit": "un",
      "sku": null,
      "notes": ""
    }
  ],
  "warnings": []
}

Reglas de líneas (carátula):
- Cada renglón de producto es una línea. El nombre está en la columna Productos.
- La cantidad está en Ingresos. Es el número de la derecha, no la hora.
- Logicom imprime cantidades estilo 12.00 / 240.00 / 1,328.00 / -12.00
  (punto = decimal, coma = miles). 1,328.00 es mil trescientos veintiocho. 12.00 es doce.
- Si Ingresos es negativo (ajuste / anulación), cargá la línea con quantity negativa.
- NO cargues la fila de totales (1,328.00 / 252.00 / 0.00 sin nombre de producto).
- NO cargues cabeceras, RSC, VTA, Egresos, ni la hora como si fueran producto.
- NO separes la fecha/hora (13/08/2026 12:34) como línea.
- Conservá el nombre en mayúsculas como está en el papel (es el nombre del catálogo Vivar).
- unit: en carátula casi siempre "un". Cerveza retornable = un. Kg solo si el nombre lo dice.

Reglas generales:
- Ignorá IVA, CAE, CBU, QR, subtotales, percepciones.
- No inventes productos.
- Si un renglón está tapado por la sombra, no lo adivines: listalo en warnings.
- confidence de 0 a 1.
"""


def vision_available() -> bool:
    return bool(GEMINI_API_KEY)


def _prepare_jpeg_bytes(path: Path, max_side: int = 2048) -> bytes:
    from PIL import Image

    try:
        import pillow_heif

        pillow_heif.register_heif_opener()
    except Exception:
        pass

    image = Image.open(path)
    image = image.convert("RGB")
    w, h = image.size
    scale = min(1.0, max_side / float(max(w, h)))
    if scale < 1.0:
        image = image.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    image.save(buf, format="JPEG", quality=85, optimize=True)
    return buf.getvalue()


def _parse_json(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start >= 0 and end > start:
        cleaned = cleaned[start : end + 1]
    return json.loads(cleaned)


def parse_logicom_number(value: Any) -> float | None:
    """12.00 → 12 · 1,328.00 → 1328 · -12.00 → -12 · 1.328,00 → 1328."""
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace(" ", "")
    if not text:
        return None
    neg = text.startswith("-") or text.startswith("(")
    text = text.strip("-() ")
    if re.fullmatch(r"\d{1,3}(,\d{3})+(\.\d+)?", text):
        text = text.replace(",", "")
    elif re.fullmatch(r"\d{1,3}(\.\d{3})+(,\d+)?", text):
        text = text.replace(".", "").replace(",", ".")
    elif "," in text and "." not in text:
        text = text.replace(",", ".")
    try:
        n = float(text)
    except ValueError:
        return None
    return -n if neg else n


_JUNK_NAME = re.compile(
    r"^(total|ingresos|egresos|descripcion|productos|comprobante|usuario|"
    r"fecha|hora|proceso|rsc|vta|mov|dep|subtotal)\b",
    re.I,
)
_LOOKS_DATETIME = re.compile(r"^\d{1,2}[/-]\d{1,2}[/-]\d{2,4}")


def _fold_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (name or "").lower()).strip()


def _clean_product_name(name: str) -> str:
    text = re.sub(r"^\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\s+\d{1,2}:\d{2}\s*", "", name or "")
    text = re.sub(r"\s+", " ", text).strip(" .-")
    return text


def _compose_header(payload: dict[str, Any]) -> tuple[str, str]:
    source = str(payload.get("source_system") or "").strip().upper()
    if source not in {"LOGICOM", "LOGEX"}:
        source = ""
    supplier = str(payload.get("supplier") or "").strip()
    if source and (not supplier or supplier.upper() in {"LOGICOM", "LOGEX", "SÚPER VIVAR", "SUPER VIVAR"}):
        supplier = f"Ingreso {source}"
    elif not supplier and payload.get("document_type") == "caratula":
        supplier = "Ingreso interno"
    caratula = str(payload.get("caratula_number") or "").strip()
    fc = str(payload.get("document_number") or "").strip()
    fc = re.sub(r"^(FC|FACTURA|REMITO)\s*[:#]?\s*", "", fc, flags=re.I)
    if caratula and fc:
        number = f"C-{caratula} · FC {fc}"
    elif caratula:
        number = f"C-{caratula}"
    else:
        number = fc
    return supplier, number


def _normalize_lines(raw_lines: Any) -> list[dict[str, Any]]:
    lines: list[dict[str, Any]] = []
    for raw in raw_lines or []:
        if not isinstance(raw, dict):
            continue
        name = _clean_product_name(str(raw.get("name") or ""))
        if not name or _JUNK_NAME.match(name) or _LOOKS_DATETIME.match(name):
            continue
        quantity = parse_logicom_number(raw.get("quantity"))
        if quantity is None:
            continue
        unit = str(raw.get("unit") or "un").strip().lower()
        if unit in {"u", "unid", "unidad", "unidades", "pza", "pz"}:
            unit = "un"
        elif unit in {"l", "lts", "litro", "litros"}:
            unit = "lt"
        elif unit in {"kilo", "kilos", "kgs"}:
            unit = "kg"
        elif unit in {"caja", "cajas"}:
            unit = "cj"
        lines.append(
            {
                "name": name,
                "quantity": quantity,
                "unit": unit or "un",
                "sku": raw.get("sku"),
                "notes": str(raw.get("notes") or "").strip(),
            }
        )
    return lines


def net_adjustments(lines: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    """Suma ingresos y ajustes negativos del mismo producto."""
    buckets: "OrderedDict[str, dict[str, Any]]" = OrderedDict()
    order: list[str] = []
    warnings: list[str] = []
    for line in lines:
        key = _fold_name(line["name"])
        if key not in buckets:
            buckets[key] = dict(line)
            order.append(key)
            continue
        buckets[key]["quantity"] = float(buckets[key]["quantity"]) + float(line["quantity"])
        if float(line["quantity"]) < 0:
            note = f"ajuste {line['quantity']:g}"
            prev = buckets[key].get("notes") or ""
            buckets[key]["notes"] = f"{prev} · {note}".strip(" ·")
    out = []
    for key in order:
        row = buckets[key]
        qty = float(row["quantity"])
        if qty <= 0:
            warnings.append(f"«{row['name']}» quedó en {qty:g} después del ajuste. No entra al ingreso.")
            continue
        if qty != int(qty):
            row["quantity"] = round(qty, 3)
        else:
            row["quantity"] = int(qty)
        out.append(row)
    return out, warnings


def normalize(payload: dict[str, Any]) -> dict[str, Any]:
    lines = _normalize_lines(payload.get("lines"))
    lines, net_warn = net_adjustments(lines)
    supplier, number = _compose_header(payload)
    confidence = payload.get("confidence")
    try:
        confidence = float(confidence) if confidence is not None else None
    except (TypeError, ValueError):
        confidence = None
    date_val = payload.get("document_date") or None
    if date_val:
        date_val = str(date_val)[:10]
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date_val):
            date_val = None
    warnings = [str(w) for w in (payload.get("warnings") or []) if str(w).strip()]
    warnings.extend(net_warn)
    dtype = str(payload.get("document_type") or "").strip().lower() or None
    return {
        "document_type": dtype,
        "source_system": str(payload.get("source_system") or "").strip().upper() or None,
        "caratula_number": str(payload.get("caratula_number") or "").strip() or None,
        "operator": str(payload.get("operator") or "").strip() or None,
        "supplier": supplier,
        "document_number": number,
        "document_date": date_val,
        "confidence": confidence,
        "lines": lines,
        "warnings": warnings,
        "raw": payload,
    }


def extract_document(image_path: Path) -> dict[str, Any]:
    """Lee una carátula / remito con Gemini. Sin clave, estructura vacía."""
    empty = {
        "document_type": None,
        "source_system": None,
        "caratula_number": None,
        "operator": None,
        "supplier": "",
        "document_number": "",
        "document_date": None,
        "confidence": None,
        "lines": [],
        "warnings": [],
        "raw_text": "",
    }
    if not GEMINI_API_KEY:
        empty["warnings"] = [
            "Visión no configurada. Definí GEMINI_API_KEY para leer la foto."
        ]
        return empty

    try:
        jpeg = _prepare_jpeg_bytes(image_path)
    except Exception as exc:
        empty["warnings"] = [f"No se pudo preparar la imagen: {exc}"]
        return empty

    try:
        from google import genai
        from google.genai import types
    except Exception as exc:
        empty["warnings"] = [f"No se pudo cargar el SDK de Gemini: {exc}"]
        return empty

    client = genai.Client(api_key=GEMINI_API_KEY)
    tried: list[str] = []
    last_error = ""
    for model in _model_candidates():
        tried.append(model)
        try:
            response = client.models.generate_content(
                model=model,
                contents=[
                    EXTRACT_PROMPT,
                    types.Part.from_bytes(data=jpeg, mime_type="image/jpeg"),
                ],
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    response_mime_type="application/json",
                ),
            )
            text = getattr(response, "text", None) or ""
            if not text:
                last_error = f"{model}: sin texto"
                continue
            parsed = normalize(_parse_json(text))
            parsed["raw_text"] = text
            if model != GEMINI_MODEL:
                parsed["warnings"].append(f"Modelo activo: {model}")
            if not parsed["lines"]:
                parsed["warnings"].append("La lectura no encontró líneas de producto.")
            return parsed
        except Exception as exc:
            last_error = f"{model}: {exc}"
            if not _is_missing_model(exc):
                empty["warnings"] = [f"La lectura falló: {exc}"]
                empty["raw_text"] = str(exc)
                return empty

    empty["warnings"] = [
        f"Ningún modelo Gemini respondió ({', '.join(tried)}). Último error: {last_error}"
    ]
    empty["raw_text"] = last_error
    return empty


def _model_candidates() -> list[str]:
    ordered: list[str] = []
    for name in (GEMINI_MODEL, *GEMINI_MODEL_FALLBACKS):
        if name and name not in ordered:
            ordered.append(name)
    return ordered


def _is_missing_model(exc: Exception) -> bool:
    text = str(exc).lower()
    return any(
        token in text
        for token in (
            "not found",
            "not_found",
            "404",
            "is not found for api version",
            "not supported for generatecontent",
            "no longer available",
            "not available to new users",
            "not available",
            "unavailable",
            "deprecated",
            "retired",
            "has been shut down",
            "failed_precondition",
        )
    )
