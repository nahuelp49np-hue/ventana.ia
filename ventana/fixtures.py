"""Carátulas reales de Súper Vivar — 13.08.2026. Calibración de lectura."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from ventana.config import ROOT
from ventana.vision import normalize

FIXTURE_DIR = ROOT / "data" / "fixtures"

# Lectura de oro de las dos fotos de depósito (sombra incluida).
# Totales ignorados. Topline Ultra Red Berry: 24 + (-12) = 12.
_RAW = {
    "caratula-1652": {
        "document_type": "caratula",
        "source_system": "LOGEX",
        "caratula_number": "1652",
        "operator": "JoseG",
        "supplier": "LOGEX",
        "document_number": "6-1425109",
        "document_date": "2026-08-13",
        "confidence": 1.0,
        "lines": [
            {"name": "CERVEZA AMSTEL LAGER RETORNABLE X1LT", "quantity": 12, "unit": "un"},
            {"name": "CERVEZA AMSTEL LAGER LATA 473cc.Nva.", "quantity": 240, "unit": "un"},
        ],
        "warnings": [],
    },
    "caratula-1647": {
        "document_type": "caratula",
        "source_system": "LOGICOM",
        "caratula_number": "1647",
        "operator": "JoseG",
        "supplier": "LOGICOM",
        "document_number": "14-712036",
        "document_date": "2026-08-13",
        "confidence": 1.0,
        "lines": [
            {"name": "BANO REPOS.AGUILA NUT AVELLANA 290gr.", "quantity": 3, "unit": "un"},
            {"name": "ALFAJOR GOAT BONOBON X75GR", "quantity": 42, "unit": "un"},
            {"name": "ALFAJOR MINITORTA DARK AGUILA X69GR", "quantity": 21, "unit": "un"},
            {"name": "ALFAJOR AGUILA MINITORTA BROWNIE 71.5gr.", "quantity": 21, "unit": "un"},
            {"name": "ALFAJOR AGUILA MINITORTA CLAS.69gr.", "quantity": 21, "unit": "un"},
            {"name": "COFLER ARCOR GRAFFITI BLANCO 45gr", "quantity": 12, "unit": "un"},
            {"name": "COFLER ARCOR GRAFFITI 45gr.", "quantity": 12, "unit": "un"},
            {"name": "CHOCOLATE COFLER ESTILO DUBAI X43G", "quantity": 20, "unit": "un"},
            {"name": "MOGUL EXTREME SANDIA X80GR", "quantity": 6, "unit": "un"},
            {"name": "MOGUL ARCOR MORAS 80gr.", "quantity": 6, "unit": "un"},
            {"name": "MOGUL ARCOR ANILLOS 80gr.", "quantity": 6, "unit": "un"},
            {"name": "PASTILLA GOMA MOGUL JELLY BEANS 80gr.", "quantity": 6, "unit": "un"},
            {"name": "PASTILLA GOMA MOGUL DIENTES 80gr.", "quantity": 6, "unit": "un"},
            {"name": "MOGUL LADRILLOS EXTREME FRUTILLA X100GR", "quantity": 6, "unit": "un"},
            {"name": "CHICLE TOPLINE 7 STRONG 14gr.", "quantity": 32, "unit": "un"},
            {"name": "CHICLE TOPLINE 7 MINT 14gr.", "quantity": 32, "unit": "un"},
            {"name": "CHICLE TOPLINE 7 STRAWBERRY", "quantity": 2, "unit": "un"},
            {"name": "CHICLE TOP LINE STRONG x1Uni 6.7g", "quantity": 40, "unit": "un"},
            {"name": "CHICLE TOPLINE 7 MENTHOL", "quantity": 2, "unit": "un"},
            {"name": "CHICLE TOPLINE 7 MANDARINE 14gr.", "quantity": 32, "unit": "un"},
            {"name": "CHICLE TOPLINE 7 BUBBLE FUN 14gr.", "quantity": 32, "unit": "un"},
            {"name": "CHICLE TOPLINE 7 ULTR/RED BERRY 24gr.", "quantity": 24, "unit": "un"},
            {"name": "CHICLE TOPLINE 7 ULTR/RED BERRY 24gr.", "quantity": -12, "unit": "un"},
            {"name": "CHICLE TOPLINE 7SEVEN ULTRA GREEN MINT", "quantity": 12, "unit": "un"},
            {"name": "TURRON ARCOR 25gr.", "quantity": 600, "unit": "un"},
            {"name": "TURROCKETS ARCOR 25gr.", "quantity": 200, "unit": "un"},
            {"name": "ROCKLETS CHOCOLATE CONFITADO 20gr.", "quantity": 48, "unit": "un"},
            {"name": "MINI ROCKLETS X 10 GS.", "quantity": 44, "unit": "un"},
            {"name": "ROCKLETS CHOCOLATE CONFITADO 40gr.", "quantity": 36, "unit": "un"},
            {"name": "ROCKLETS MANI C/CHOCO.CONF.40gr.", "quantity": 16, "unit": "un"},
        ],
        "warnings": [],
    },
}

META = {
    "caratula-1652": {
        "title": "Carátula 1652 · Logex · Amstel",
        "image": "caratula-1652.jpg",
        "source": "WhatsApp Image 2026-08-13 at 18.53.38(1).jpeg",
    },
    "caratula-1647": {
        "title": "Carátula 1647 · Logicom · golosinas Arcor",
        "image": "caratula-1647.jpg",
        "source": "WhatsApp Image 2026-08-13 at 18.53.38.jpeg",
    },
}


def list_examples() -> list[dict[str, str]]:
    return [{"slug": slug, **meta} for slug, meta in META.items()]


def image_path(slug: str) -> Path | None:
    meta = META.get(slug)
    if not meta:
        return None
    path = FIXTURE_DIR / meta["image"]
    return path if path.exists() else None


def load_example(slug: str) -> dict[str, Any] | None:
    raw = _RAW.get(slug)
    if not raw:
        return None
    parsed = normalize(deepcopy(raw))
    parsed["raw_text"] = f"fixture:{slug}"
    return parsed
