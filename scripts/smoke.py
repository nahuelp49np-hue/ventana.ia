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
        assert "carátula" in r.text.lower()
        assert "Carátula 1652" in r.text

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
        assert "Leche Tregar" in r.text

        r = client.get("/capturar/ejemplo/caratula-1652", follow_redirects=False)
        assert r.status_code == 303
        loc = r.headers["location"]
        r = client.get(loc)
        assert r.status_code == 200
        assert "C-1652" in r.text
        assert "CERVEZA AMSTEL LAGER RETORNABLE X1LT" in r.text
        assert "CERVEZA AMSTEL LAGER LATA 473cc.Nva" in r.text
        assert "240" in r.text
        assert r.text.count("prod-card") >= 2
        assert r.text.count("prod-card") >= 2
        assert "data-line-none" in r.text
        assert "Aplicar vencimiento a todas" not in r.text
        intake_amstel = loc.rsplit("/", 1)[-1]
        r = client.post(
            f"/ingreso/{intake_amstel}/confirmar",
            data={
                "supplier": "Ingreso LOGEX",
                "document_number": "C-1652 · FC 6-1425109",
                "document_date": "2026-08-13",
                "line_name": [
                    "CERVEZA AMSTEL LAGER RETORNABLE X1LT",
                    "CERVEZA AMSTEL LAGER LATA 473cc.Nva",
                ],
                "line_qty": ["12", "240"],
                "line_unit": ["un", "un"],
                "line_expires": ["2026-11-13", ""],
                "line_novence": ["0", "1"],
                "line_notes": ["", ""],
                "line_product_id": ["", ""],
            },
            follow_redirects=False,
        )
        assert r.status_code == 303, r.text
        r = client.get("/control")
        assert "AMSTEL LAGER RETORNABLE" in r.text or "Amstel" in r.text
        assert "no vence" in r.text.lower()

        from ventana.fixtures import image_path, load_example
        from ventana.recognize import match_known_caratula
        from ventana.vision import net_adjustments, parse_logicom_number

        amstel_img = image_path("caratula-1652")
        assert amstel_img and match_known_caratula(amstel_img) == "caratula-1652"
        with amstel_img.open("rb") as fh:
            r = client.post(
                "/capturar",
                files={"foto": ("caratula-1652.jpg", fh, "image/jpeg")},
                follow_redirects=False,
            )
        assert r.status_code == 303
        r = client.get(r.headers["location"])
        assert "CERVEZA AMSTEL LAGER RETORNABLE X1LT" in r.text
        assert "12" in r.text
        assert "240" in r.text

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
        gold = load_example("caratula-1647")
        assert gold is not None
        assert gold["document_number"].startswith("C-1647")
        assert len(gold["lines"]) == 29
        assert any("ajuste" in (ln.get("notes") or "") for ln in gold["lines"])

        print("SYS.VENTANA  ·  SMOKE OK")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
