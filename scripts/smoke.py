"""Smoke de activación — no es suite, es prueba de que el sistema respira."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient

from ventana.web import app


def main() -> int:
    with TestClient(app) as client:
        r = client.get("/salud")
        assert r.status_code == 200, r.text
        assert r.json()["system"] == "SYS.VENTANA"

        r = client.get("/control", follow_redirects=False)
        assert r.status_code == 303

        r = client.get("/acceso")
        assert r.status_code == 200
        assert "ventana" in r.text
        assert "hecho por runa" in r.text.lower()

        r = client.post("/acceso", data={"username": "deposito", "password": "mal"}, follow_redirects=False)
        assert r.status_code == 303

        r = client.post("/acceso", data={"username": "deposito", "password": "vivar"}, follow_redirects=False)
        assert r.status_code == 303
        assert r.headers["location"] == "/control"

        r = client.get("/control")
        assert r.status_code == 200
        assert "CONTROL DE VIDA ÚTIL" in r.text
        assert "CRÍTICO" in r.text or "Crítico" in r.text

        r = client.get("/capturar")
        assert r.status_code == 200
        assert "Leer productos" in r.text
        assert "Carátula 1652" not in r.text
        assert "Amstel" not in r.text
        assert "1647" not in r.text

        r = client.post("/capturar", follow_redirects=False)
        assert r.status_code == 303
        assert r.headers["location"] == "/capturar"

        r = client.get("/ingreso/manual", follow_redirects=False)
        assert r.status_code == 303
        loc = r.headers["location"]
        assert loc.startswith("/ingreso/")
        intake_id = loc.rsplit("/", 1)[-1]

        r = client.get(loc)
        assert r.status_code == 200
        assert "UN VENCIMIENTO POR PRODUCTO" in r.text
        assert "No vence" in r.text
        assert "data-line-shift" in r.text

        r = client.post(
            f"/ingreso/{intake_id}/confirmar",
            data={
                "supplier": "La Paulina",
                "document_number": "R-0001",
                "document_date": "2026-08-13",
                "line_name": "Manteca La Paulina 200g",
                "line_qty": "12",
                "line_unit": "un",
                "line_expires": "2026-09-10",
                "line_notes": "smoke",
                "line_product_id": "",
            },
            follow_redirects=False,
        )
        assert r.status_code == 303, r.text
        assert r.headers["location"] == "/control"

        r = client.get("/control")
        assert "Manteca La Paulina" in r.text

        r = client.get("/historial")
        assert r.status_code == 200
        assert "ingresar" in r.text

        r = client.get("/protocolo", follow_redirects=False)
        assert r.status_code == 303  # deposito no entra

        client.post("/salir")
        r = client.post("/acceso", data={"username": "admin", "password": "runa"}, follow_redirects=False)
        assert r.status_code == 303
        r = client.get("/protocolo")
        assert r.status_code == 200
        assert "PROTOCOLO DE UMBRALES" in r.text

        r = client.get("/productos")
        assert r.status_code == 200

        r = client.get("/capturar/ejemplo/caratula-1652", follow_redirects=False)
        assert r.status_code == 404

        from ventana.vision import net_adjustments, parse_logicom_number

        assert parse_logicom_number("1,328.00") == 1328
        assert parse_logicom_number("12.00") == 12
        assert parse_logicom_number("-12.00") == -12
        netted, warns = net_adjustments(
            [
                {"name": "CHICLE TOPLINE 7 ULTR/RED BERRY 24gr.", "quantity": 24, "unit": "un", "notes": ""},
                {"name": "CHICLE TOPLINE 7 ULTR/RED BERRY 24gr.", "quantity": -12, "unit": "un", "notes": ""},
            ]
        )
        assert len(netted) == 1 and netted[0]["quantity"] == 12

        print("SYS.VENTANA  ·  SMOKE OK")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
