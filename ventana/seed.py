from __future__ import annotations

from datetime import date, timedelta

from ventana import db
from ventana.auth import hash_password

# Catálogo anclado a SKUs reales de Súper Vivar (SYS.COMMERCE).
PRODUCTS = [
    {
        "sku": "7793913001822",
        "name": "Leche Tregar Larga Vida Entera 1L",
        "category": "Lácteos",
        "unit": "un",
        "default_life_days": 90,
    },
    {
        "sku": "7793913012996",
        "name": "Leche Tregar UAT Parc.descrem. 1L",
        "category": "Lácteos",
        "unit": "un",
        "default_life_days": 90,
    },
    {
        "sku": "7790398100118",
        "name": "Queso Rallado La Paulina 40g",
        "category": "Lácteos",
        "unit": "un",
        "default_life_days": 120,
    },
    {
        "sku": "201193500000",
        "name": "La Pauli Cremoso",
        "category": "Fiambrería",
        "unit": "kg",
        "default_life_days": 25,
    },
    {
        "sku": "201154800000",
        "name": "Tregar Cremoso",
        "category": "Fiambrería",
        "unit": "kg",
        "default_life_days": 25,
    },
    {
        "sku": "201159500000",
        "name": "Picada",
        "category": "Fiambrería",
        "unit": "kg",
        "default_life_days": 8,
    },
    {
        "sku": "201714800000",
        "name": "Carne Molida",
        "category": "Carnicería",
        "unit": "kg",
        "default_life_days": 2,
    },
    {
        "sku": "12421",
        "name": "Costilla Novillo FDC",
        "category": "Carnicería",
        "unit": "kg",
        "default_life_days": 4,
    },
    {
        "sku": None,
        "name": "Ricota Tregar 500g",
        "category": "Lácteos",
        "unit": "un",
        "default_life_days": 18,
    },
    {
        "sku": None,
        "name": "Yogur bebible frutilla 900g",
        "category": "Lácteos",
        "unit": "un",
        "default_life_days": 21,
    },
    {
        "sku": None,
        "name": "Jamón cocido horma",
        "category": "Fiambrería",
        "unit": "kg",
        "default_life_days": 20,
    },
    {
        "sku": None,
        "name": "Manteca La Paulina 200g",
        "category": "Lácteos",
        "unit": "un",
        "default_life_days": 45,
    },
    # Carátulas reales 13.08 — nombres como los imprime Logicom.
    {
        "sku": "7793147573546",
        "name": "Cerveza Amstel Lager Lata 473CC.NVA.",
        "category": "Bebidas",
        "unit": "un",
        "default_life_days": 180,
    },
    {
        "sku": None,
        "name": "Cerveza Amstel Lager Retornable X1LT",
        "category": "Bebidas",
        "unit": "un",
        "default_life_days": 180,
    },
    {
        "sku": "7790040154896",
        "name": "Alfajor Goat Bonobon",
        "category": "Golosinas",
        "unit": "un",
        "default_life_days": 180,
    },
    {
        "sku": "77931764",
        "name": "Chicle Topline 7 Mint",
        "category": "Golosinas",
        "unit": "un",
        "default_life_days": 365,
    },
]


def ensure_catalog() -> None:
    """Suma productos de carátulas reales sin pisar lo que ya está."""
    have = {(p.get("sku") or "").strip() for p in db.list_products()}
    names = {_fold(p["name"]) for p in db.list_products()}
    for p in PRODUCTS:
        sku = (p.get("sku") or "").strip()
        if sku and sku in have:
            continue
        if _fold(p["name"]) in names:
            continue
        db.upsert_product(
            name=p["name"],
            sku=p["sku"],
            category=p["category"],
            unit=p["unit"],
            default_life_days=p["default_life_days"],
        )


def _fold(name: str) -> str:
    import re

    return re.sub(r"[^a-z0-9]+", " ", (name or "").lower()).strip()


def seed_if_empty() -> None:
    """Solo operadores. El depósito arranca sin lotes ni catálogo de demo."""
    if db.count_users() == 0:
        db.create_user("deposito", hash_password("vivar"), "deposito", "Depósito")
        db.create_user("admin", hash_password("runa"), "admin", "Administración")
