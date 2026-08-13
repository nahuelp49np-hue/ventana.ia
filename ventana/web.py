from __future__ import annotations

import re
import shutil
import uuid
from contextlib import asynccontextmanager
from datetime import date, datetime
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, Request, UploadFile
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from ventana import alerts, db
from ventana.auth import (
    admin_required,
    current_user,
    hash_password,
    login_required,
    verify_password,
)
from ventana.config import (
    ALLOWED_IMAGE_EXT,
    APP_NAME,
    MAX_UPLOAD_BYTES,
    ROOT,
    SECRET_KEY,
    STORE_NAME,
    SYSTEM_CODE,
    SYSTEM_INDEX,
    TZ_NAME,
    UPLOAD_DIR,
)
from ventana.fixtures import image_path as fixture_image, list_examples, load_example
from ventana.recognize import extract_known
from ventana.risk import LABELS, NO_EXPIRY, STATUS_LABELS, annotate, days_left, is_non_expiring
from ventana.seed import seed_if_empty
from ventana.vision import extract_document, vision_available

scheduler: BackgroundScheduler | None = None


@asynccontextmanager
async def lifespan(_: FastAPI):
    global scheduler
    db.init_db()
    seed_if_empty()
    scheduler = BackgroundScheduler(timezone=TZ_NAME)
    scheduler.add_job(
        alerts.dispatch,
        "interval",
        minutes=15,
        kwargs={"immediate_only": True},
        id="urgent",
        replace_existing=True,
    )
    scheduler.add_job(
        alerts.maybe_daily_digest,
        "interval",
        minutes=1,
        id="digest",
        replace_existing=True,
    )
    scheduler.start()
    yield
    if scheduler:
        scheduler.shutdown(wait=False)


app = FastAPI(title="ventana.ia", docs_url=None, redoc_url=None, lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY, same_site="lax", https_only=False)
app.mount("/static", StaticFiles(directory=str(ROOT / "static")), name="static")

templates = Jinja2Templates(directory=str(ROOT / "templates"))


def _tz() -> ZoneInfo:
    try:
        return ZoneInfo(db.get_setting("timezone", TZ_NAME) or TZ_NAME)
    except Exception:
        return ZoneInfo("America/Argentina/Buenos_Aires")


def today() -> date:
    return datetime.now(_tz()).date()


def fmt_date(value: Any) -> str:
    if not value:
        return "—"
    text = str(value)[:10]
    parts = text.split("-")
    if len(parts) == 3:
        return f"{parts[2]}.{parts[1]}"
    return text


def fmt_qty(value: Any, unit: Any = "") -> str:
    try:
        n = float(value)
    except (TypeError, ValueError):
        return "—"
    if n == int(n):
        body = str(int(n))
    else:
        body = f"{n:.2f}".rstrip("0").rstrip(".").replace(".", ",")
    return f"{body} {unit}".strip() if unit else body


def fmt_dt(value: Any) -> str:
    if not value:
        return "—"
    text = str(value).replace("T", " ")
    return text[:16]


templates.env.filters["d"] = fmt_date
templates.env.filters["q"] = fmt_qty
templates.env.filters["dt"] = fmt_dt
templates.env.globals["LABELS"] = LABELS
templates.env.globals["STATUS_LABELS"] = STATUS_LABELS
templates.env.globals["APP_NAME"] = APP_NAME
templates.env.globals["SYSTEM_CODE"] = SYSTEM_CODE
templates.env.globals["SYSTEM_INDEX"] = SYSTEM_INDEX


def flash(request: Request, message: str, tone: str = "ok") -> None:
    request.session["flash"] = {"message": message, "tone": tone}


def pop_flash(request: Request) -> dict[str, str] | None:
    return request.session.pop("flash", None)


def ctx(request: Request, **extra: Any) -> dict[str, Any]:
    user = current_user(request)
    settings = db.get_settings()
    base = {
        "request": request,
        "user": user,
        "flash": pop_flash(request),
        "vision_on": vision_available(),
        "store_name": settings.get("store_name") or STORE_NAME,
        "nav": extra.pop("nav", ""),
        "page_title": extra.pop("page_title", APP_NAME),
        "kicker_index": extra.pop("kicker_index", SYSTEM_INDEX),
        "kicker": extra.pop("kicker", "CONTROL"),
    }
    base.update(extra)
    return base


def _fold(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (name or "").lower()).strip()


def match_product(name: str, products: list[dict[str, Any]]) -> tuple[dict[str, Any] | None, float]:
    n = _fold(name)
    if not n:
        return None, 0.0
    best: dict[str, Any] | None = None
    score = 0.0
    tokens = set(n.split())
    for p in products:
        pn = _fold(p.get("name") or "")
        s = SequenceMatcher(None, n, pn).ratio()
        if n in pn or pn in n:
            s = max(s, 0.86)
        pt = set(pn.split())
        if tokens and pt:
            s = max(s, len(tokens & pt) / len(tokens | pt))
        sku = (p.get("sku") or "").lower()
        if sku and sku in n:
            s = max(s, 0.93)
        if s > score:
            best, score = p, s
    if best and score >= 0.52:
        return best, score
    return None, score


def counts_from(batches: list[dict[str, Any]]) -> dict[str, int]:
    out = {
        "vencido": 0,
        "critico": 0,
        "advertencia": 0,
        "preventivo": 0,
        "estable": 0,
        "sin_vence": 0,
        "promocion": 0,
        "total": len(batches),
    }
    for b in batches:
        out[b["level"]] = out.get(b["level"], 0) + 1
        if b.get("status") == "promocion":
            out["promocion"] += 1
    return out


# ——— routes ———


@app.get("/salud")
async def salud():
    return {"system": SYSTEM_CODE, "ok": True, "vision": vision_available()}


@app.get("/")
async def root(request: Request):
    if current_user(request):
        return RedirectResponse("/control", status_code=303)
    return RedirectResponse("/acceso", status_code=303)


@app.get("/acceso")
async def acceso_get(request: Request):
    if current_user(request):
        return RedirectResponse("/control", status_code=303)
    return templates.TemplateResponse(
        "acceso.html",
        ctx(request, nav="acceso", page_title="acceso — ventana.ia", kicker="PROTOCOLO DE ACCESO", kicker_index="00"),
    )


@app.post("/acceso")
async def acceso_post(request: Request):
    form = await request.form()
    username = str(form.get("username") or "").strip().lower()
    password = str(form.get("password") or "")
    user = db.get_user_by_username(username)
    if not user or not verify_password(password, user["password_hash"]):
        flash(request, "Acceso denegado.", "critico")
        return RedirectResponse("/acceso", status_code=303)
    db.touch_login(user["id"])
    request.session["user"] = {
        "id": user["id"],
        "username": user["username"],
        "role": user["role"],
        "display_name": user["display_name"],
    }
    return RedirectResponse("/control", status_code=303)


@app.post("/salir")
async def salir(request: Request):
    request.session.clear()
    return RedirectResponse("/acceso", status_code=303)


@app.get("/control")
@login_required
async def control(request: Request):
    th = db.thresholds()
    live = [annotate(b, th, today()) for b in db.list_batches(status_in=("activo", "promocion"))]
    filtro = (request.query_params.get("v") or "todos").lower()
    shown = live
    if filtro == "critico":
        shown = [b for b in live if b["level"] in {"vencido", "critico"}]
    elif filtro == "advertencia":
        shown = [b for b in live if b["level"] == "advertencia"]
    elif filtro == "preventivo":
        shown = [b for b in live if b["level"] == "preventivo"]
    elif filtro == "promocion":
        shown = [b for b in live if b.get("status") == "promocion"]
    elif filtro == "estable":
        shown = [b for b in live if b["level"] == "estable"]
    return templates.TemplateResponse(
        "control.html",
        ctx(
            request,
            nav="control",
            page_title="control — ventana.ia",
            kicker="CONTROL DE VIDA ÚTIL",
            batches=shown,
            counts=counts_from(live),
            filtro=filtro,
            thresholds=th,
        ),
    )


def _intake_from_extraction(user: dict[str, Any] | None, extracted: dict[str, Any], photo_path: str | None) -> int:
    products = db.list_products()
    intake_id = db.create_intake(
        photo_path=photo_path,
        supplier=extracted.get("supplier") or "",
        document_number=extracted.get("document_number") or "",
        document_date=extracted.get("document_date"),
        raw_ocr=extracted.get("raw_text"),
        confidence=extracted.get("confidence"),
        warnings=extracted.get("warnings") or [],
        created_by=user["id"] if user else None,
    )
    lines = extracted.get("lines") or []
    if not lines:
        return intake_id
    for i, line in enumerate(lines):
        matched, _ = match_product(line["name"], products)
        db.add_intake_line(
            intake_id,
            line["name"],
            line.get("quantity") or 1,
            line.get("unit") or "un",
            product_id=matched["id"] if matched else None,
            notes=line.get("notes") or "",
            sort_order=i,
        )
    return intake_id


@app.get("/capturar")
@login_required
async def capturar_get(request: Request):
    return templates.TemplateResponse(
        "capturar.html",
        ctx(
            request,
            nav="capturar",
            page_title="captura — ventana.ia",
            kicker="CAPTURA DE INGRESO",
            kicker_index="01",
            examples=list_examples(),
        ),
    )


def _save_upload(upload: UploadFile) -> Path | None:
    filename = upload.filename or "remito.jpg"
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_IMAGE_EXT:
        ext = ".jpg"
    dest = UPLOAD_DIR / f"{date.today().isoformat()}_{uuid.uuid4().hex[:10]}{ext}"
    with dest.open("wb") as fh:
        shutil.copyfileobj(upload.file, fh)
    if dest.stat().st_size > MAX_UPLOAD_BYTES:
        dest.unlink(missing_ok=True)
        return None
    return dest


@app.post("/capturar")
@login_required
async def capturar_post(request: Request):
    user = current_user(request)
    form = await request.form()
    raw_foto = form.get("foto")
    if raw_foto is None:
        files = [v for v in form.values() if hasattr(v, "filename")]
        raw_foto = files[0] if files else None
    if isinstance(raw_foto, UploadFile):
        foto = raw_foto
    elif raw_foto is not None and hasattr(raw_foto, "filename"):
        foto = raw_foto
    else:
        foto = None
    if not (foto and (getattr(foto, "filename", None) or "")):
        flash(request, "Elegí una foto o tocá una carátula de ejemplo.", "advertencia")
        return RedirectResponse("/capturar", status_code=303)
    saved = _save_upload(foto)
    if not saved:
        flash(request, "La foto supera 12 MB o no se pudo guardar.", "advertencia")
        return RedirectResponse("/capturar", status_code=303)
    photo_path = str(saved.relative_to(ROOT)).replace("\\", "/")
    extracted = extract_known(saved)
    if not extracted:
        extracted = extract_document(saved)
    if not (extracted.get("lines") or []):
        flash(
            request,
            "No se leyeron productos. Tocá la carátula de ejemplo (Amstel / Arcor) o configurá la visión.",
            "critico",
        )
        return RedirectResponse("/capturar", status_code=303)
    intake_id = _intake_from_extraction(user, extracted, photo_path)
    return RedirectResponse(f"/ingreso/{intake_id}", status_code=303)


@app.get("/capturar/ejemplo/{slug}")
@app.post("/capturar/ejemplo/{slug}")
@login_required
async def capturar_ejemplo(request: Request, slug: str):
    user = current_user(request)
    extracted = load_example(slug)
    if not extracted:
        flash(request, "Esa carátula de ejemplo no existe.", "advertencia")
        return RedirectResponse("/capturar", status_code=303)
    photo_path = None
    src = fixture_image(slug)
    if src:
        dest = UPLOAD_DIR / f"fixture_{slug}_{uuid.uuid4().hex[:8]}{src.suffix}"
        shutil.copyfile(src, dest)
        photo_path = str(dest.relative_to(ROOT)).replace("\\", "/")
    extracted.setdefault("warnings", [])
    extracted["warnings"] = [
        "Lectura de oro de carátula real (13.08). La visión, cuando esté encendida, usa esta misma regla."
    ] + list(extracted.get("warnings") or [])
    intake_id = _intake_from_extraction(user, extracted, photo_path)
    flash(request, "Carátula de ejemplo cargada. Asigná vencimiento y confirmá.", "ok")
    return RedirectResponse(f"/ingreso/{intake_id}", status_code=303)


@app.get("/ingreso/manual")
@login_required
async def ingreso_manual(request: Request):
    user = current_user(request)
    intake_id = db.create_intake(
        photo_path=None,
        supplier="",
        document_number="",
        document_date=today().isoformat(),
        raw_ocr=None,
        confidence=None,
        warnings=[],
        created_by=user["id"] if user else None,
    )
    db.add_intake_line(intake_id, "", 1, "un")
    return RedirectResponse(f"/ingreso/{intake_id}", status_code=303)


@app.get("/ingreso/{intake_id}")
@login_required
async def ingreso_get(request: Request, intake_id: int):
    intake = db.get_intake(intake_id)
    if not intake:
        flash(request, "Ingreso no encontrado.", "advertencia")
        return RedirectResponse("/control", status_code=303)
    for line in intake.get("lines") or []:
        line["no_vence"] = is_non_expiring(line.get("expires_at"))
        if line["no_vence"]:
            line["expires_display"] = ""
        else:
            line["expires_display"] = (line.get("expires_at") or "")[:10]
    return templates.TemplateResponse(
        "ingreso.html",
        ctx(
            request,
            nav="capturar",
            page_title="revisión — ventana.ia",
            kicker="UN VENCIMIENTO POR PRODUCTO",
            kicker_index="03",
            intake=intake,
            products=db.list_products(),
            shift_days=(7, 15, 30, 60, 90, 180, 365),
        ),
    )


def _lines_from_form(form) -> list[dict[str, Any]]:
    names = form.getlist("line_name")
    qtys = form.getlist("line_qty")
    units = form.getlist("line_unit")
    exps = form.getlist("line_expires")
    notes = form.getlist("line_notes")
    pids = form.getlist("line_product_id")
    none = form.getlist("line_novence")
    lines = []
    for i, name in enumerate(names):
        raw = str(name or "").strip()
        if not raw:
            continue
        qty_s = str(qtys[i] if i < len(qtys) else "1").replace(",", ".")
        try:
            qty = float(qty_s)
        except ValueError:
            qty = 1.0
        pid_s = str(pids[i] if i < len(pids) else "").strip()
        pid = int(pid_s) if pid_s.isdigit() else None
        marked_none = str(none[i] if i < len(none) else "").strip() in {"1", "on", "true"}
        exp = str(exps[i] if i < len(exps) else "").strip() or None
        if marked_none or is_non_expiring(exp):
            exp = NO_EXPIRY
        lines.append(
            {
                "raw_name": raw,
                "quantity": qty,
                "unit": str(units[i] if i < len(units) else "un") or "un",
                "expires_at": exp,
                "notes": str(notes[i] if i < len(notes) else "").strip(),
                "product_id": pid,
                "no_vence": marked_none or is_non_expiring(exp),
            }
        )
    return lines


@app.post("/ingreso/{intake_id}")
@login_required
async def ingreso_save(request: Request, intake_id: int):
    intake = db.get_intake(intake_id)
    if not intake or intake["status"] != "borrador":
        flash(request, "Este ingreso ya no se puede editar.", "advertencia")
        return RedirectResponse("/control", status_code=303)
    form = await request.form()
    db.update_intake_header(
        intake_id,
        str(form.get("supplier") or "").strip(),
        str(form.get("document_number") or "").strip(),
        str(form.get("document_date") or "").strip() or None,
    )
    db.replace_intake_lines(intake_id, _lines_from_form(form))
    flash(request, "Borrador guardado.", "ok")
    return RedirectResponse(f"/ingreso/{intake_id}", status_code=303)


@app.post("/ingreso/{intake_id}/confirmar")
@login_required
async def ingreso_confirmar(request: Request, intake_id: int):
    user = current_user(request)
    intake = db.get_intake(intake_id)
    if not intake or intake["status"] != "borrador":
        flash(request, "Este ingreso ya no se puede confirmar.", "advertencia")
        return RedirectResponse("/control", status_code=303)
    form = await request.form()
    db.update_intake_header(
        intake_id,
        str(form.get("supplier") or "").strip(),
        str(form.get("document_number") or "").strip(),
        str(form.get("document_date") or "").strip() or None,
    )
    lines = _lines_from_form(form)
    db.replace_intake_lines(intake_id, lines)
    missing = [ln for ln in lines if not ln.get("expires_at") and not ln.get("no_vence")]
    if not lines:
        flash(request, "No hay productos para activar.", "advertencia")
        return RedirectResponse(f"/ingreso/{intake_id}", status_code=303)
    if missing:
        flash(
            request,
            f"{len(missing)} producto(s) sin ventana. Asigná fecha o marcá «No vence».",
            "critico",
        )
        return RedirectResponse(f"/ingreso/{intake_id}", status_code=303)

    products = db.list_products()
    received = str(form.get("document_date") or "").strip() or today().isoformat()
    created = 0
    for ln in lines:
        product = None
        if ln.get("product_id"):
            product = db.get_product(int(ln["product_id"]))
        if not product:
            matched, score = match_product(ln["raw_name"], products)
            product = matched if score >= 0.72 else None
        if not product:
            pid = db.upsert_product(
                name=ln["raw_name"],
                sku=None,
                category="",
                unit=ln["unit"],
                default_life_days=None,
            )
            product = db.get_product(pid)
            products = db.list_products()
        bid = db.create_batch(
            product_id=product["id"] if product else None,
            intake_id=intake_id,
            intake_line_id=None,
            display_name=(product["name"] if product else ln["raw_name"]),
            sku=product.get("sku") if product else None,
            category=product.get("category") if product else "",
            quantity=ln["quantity"],
            unit=ln["unit"] or (product.get("unit") if product else "un"),
            received_at=received,
            expires_at=ln["expires_at"],
            notes=ln.get("notes") or "",
            created_by=user["id"] if user else None,
        )
        db.log_action(
            bid,
            user["id"] if user else None,
            "ingresar",
            0,
            ln["quantity"],
            f"remito {form.get('document_number') or intake_id}",
        )
        created += 1
    db.confirm_intake(intake_id)
    flash(request, f"Ingreso activado. {created} lote(s) en control.", "ok")
    return RedirectResponse("/control", status_code=303)


@app.post("/ingreso/{intake_id}/descartar")
@login_required
async def ingreso_descartar(request: Request, intake_id: int):
    db.discard_intake(intake_id)
    flash(request, "Ingreso descartado.", "advertencia")
    return RedirectResponse("/control", status_code=303)


@app.get("/lote/{batch_id}")
@login_required
async def lote_get(request: Request, batch_id: int):
    batch = db.get_batch(batch_id)
    if not batch:
        flash(request, "Lote no encontrado.", "advertencia")
        return RedirectResponse("/control", status_code=303)
    th = db.thresholds()
    return templates.TemplateResponse(
        "lote.html",
        ctx(
            request,
            nav="control",
            page_title=f"lote {batch_id:03d} — ventana.ia",
            kicker=f"LOTE {batch_id:03d}",
            kicker_index="04",
            batch=annotate(batch, th, today()),
            actions=db.list_actions_for_batch(batch_id),
        ),
    )


@app.post("/lote/{batch_id}")
@login_required
async def lote_post(request: Request, batch_id: int):
    user = current_user(request)
    batch = db.get_batch(batch_id)
    if not batch:
        flash(request, "Lote no encontrado.", "advertencia")
        return RedirectResponse("/control", status_code=303)
    form = await request.form()
    action = str(form.get("action") or "")
    before = float(batch["quantity_current"])

    if action == "retirar":
        if batch["status"] in {"retirado", "agotado"}:
            flash(request, "El lote ya está fuera de circulación.", "advertencia")
            return RedirectResponse(f"/lote/{batch_id}", status_code=303)
        note = str(form.get("notes") or "retiro de circulación")
        db.update_batch(batch_id, status="retirado", notes=note)
        db.log_action(batch_id, user["id"] if user else None, "retirar", before, before, note)
        flash(request, "Lote retirado de circulación.", "ok")
        return RedirectResponse("/historial", status_code=303)

    if action == "promocion":
        db.update_batch(batch_id, status="promocion")
        db.log_action(batch_id, user["id"] if user else None, "promocion", before, before, "promoción activada")
        flash(request, "Promoción activada.", "ok")
        return RedirectResponse(f"/lote/{batch_id}", status_code=303)

    if action == "reactivar":
        db.update_batch(batch_id, status="activo")
        db.log_action(batch_id, user["id"] if user else None, "reactivar", before, before, "")
        flash(request, "Lote reactivado.", "ok")
        return RedirectResponse(f"/lote/{batch_id}", status_code=303)

    if action == "cantidad":
        raw = str(form.get("quantity") or "").replace(",", ".")
        try:
            qty = float(raw)
        except ValueError:
            flash(request, "Cantidad inválida.", "advertencia")
            return RedirectResponse(f"/lote/{batch_id}", status_code=303)
        if qty < 0:
            qty = 0
        status = batch["status"]
        if qty == 0 and status in {"activo", "promocion"}:
            status = "agotado"
        db.update_batch(batch_id, quantity_current=qty, status=status)
        db.log_action(
            batch_id,
            user["id"] if user else None,
            "editar_cantidad",
            before,
            qty,
            str(form.get("notes") or ""),
        )
        flash(request, "Cantidad actualizada.", "ok")
        dest = "/historial" if status == "agotado" else f"/lote/{batch_id}"
        return RedirectResponse(dest, status_code=303)

    if action == "notas":
        note = str(form.get("notes") or "")
        db.update_batch(batch_id, notes=note)
        flash(request, "Notas actualizadas.", "ok")
        return RedirectResponse(f"/lote/{batch_id}", status_code=303)

    if action == "vence":
        exp = str(form.get("expires_at") or "").strip()
        if not exp:
            flash(request, "Fecha inválida.", "advertencia")
            return RedirectResponse(f"/lote/{batch_id}", status_code=303)
        db.update_batch(batch_id, expires_at=exp)
        db.log_action(batch_id, user["id"] if user else None, "editar_vence", before, before, exp)
        flash(request, "Vencimiento actualizado.", "ok")
        return RedirectResponse(f"/lote/{batch_id}", status_code=303)

    return RedirectResponse(f"/lote/{batch_id}", status_code=303)


@app.get("/historial")
@login_required
async def historial(request: Request):
    kind = request.query_params.get("k") or ""
    actions = db.list_actions(limit=250, kind=kind or None)
    closed = [
        annotate(b, db.thresholds(), today())
        for b in db.list_batches(status_in=("retirado", "agotado"))
    ]
    closed.sort(key=lambda b: b.get("updated_at") or "", reverse=True)
    return templates.TemplateResponse(
        "historial.html",
        ctx(
            request,
            nav="historial",
            page_title="historial — ventana.ia",
            kicker="REGISTRO DE MOVIMIENTOS",
            kicker_index="05",
            actions=actions,
            closed=closed,
            kind=kind,
        ),
    )


@app.get("/productos")
@login_required
async def productos_get(request: Request):
    q = request.query_params.get("q") or ""
    return templates.TemplateResponse(
        "productos.html",
        ctx(
            request,
            nav="productos",
            page_title="productos — ventana.ia",
            kicker="CATÁLOGO MÍNIMO",
            kicker_index="06",
            products=db.list_products(q),
            q=q,
        ),
    )


@app.post("/productos")
@login_required
async def productos_post(request: Request):
    form = await request.form()
    life = str(form.get("default_life_days") or "").strip()
    life_n = int(life) if life.isdigit() else None
    db.upsert_product(
        name=str(form.get("name") or "").strip(),
        sku=str(form.get("sku") or "").strip() or None,
        category=str(form.get("category") or "").strip(),
        unit=str(form.get("unit") or "un"),
        default_life_days=life_n,
        notes=str(form.get("notes") or ""),
    )
    flash(request, "Producto registrado.", "ok")
    return RedirectResponse("/productos", status_code=303)


@app.get("/protocolo")
@admin_required
async def protocolo_get(request: Request):
    return templates.TemplateResponse(
        "protocolo.html",
        ctx(
            request,
            nav="protocolo",
            page_title="protocolo — ventana.ia",
            kicker="PROTOCOLO DE UMBRALES",
            kicker_index="07",
            settings=db.get_settings(),
            vision_on=vision_available(),
        ),
    )


@app.post("/protocolo")
@admin_required
async def protocolo_post(request: Request):
    form = await request.form()
    db.set_settings(
        {
            "store_name": str(form.get("store_name") or "Súper Vivar").strip(),
            "threshold_critico": str(int(form.get("threshold_critico") or 2)),
            "threshold_advertencia": str(int(form.get("threshold_advertencia") or 7)),
            "threshold_preventivo": str(int(form.get("threshold_preventivo") or 15)),
            "telegram_enabled": "1" if form.get("telegram_enabled") else "0",
            "telegram_bot_token": str(form.get("telegram_bot_token") or "").strip(),
            "telegram_chat_id": str(form.get("telegram_chat_id") or "").strip(),
            "alert_hour": str(form.get("alert_hour") or "08:00").strip(),
            "digest_include_preventivo": "1" if form.get("digest_include_preventivo") else "0",
        }
    )
    flash(request, "Protocolo actualizado.", "ok")
    return RedirectResponse("/protocolo", status_code=303)


@app.post("/protocolo/probar")
@admin_required
async def protocolo_probar(request: Request):
    live = alerts.live_batches()
    grouped = alerts.group_by_level(live)
    sample = grouped.get("critico") or grouped.get("vencido") or grouped.get("advertencia") or live[:4]
    level = sample[0]["level"] if sample else "estable"
    text = alerts.format_signal(level, sample, title="SYS.VENTANA  ·  PRUEBA DE SEÑAL")
    ok, detail = alerts.send_telegram(text)
    db.log_alert(None, "prueba", "telegram", text if ok else detail, "enviado" if ok else "error")
    if ok:
        flash(request, "Señal de prueba enviada.", "ok")
    else:
        flash(request, f"No se pudo enviar: {detail}", "critico")
    return RedirectResponse("/protocolo", status_code=303)


@app.get("/usuarios")
@admin_required
async def usuarios_get(request: Request):
    return templates.TemplateResponse(
        "usuarios.html",
        ctx(
            request,
            nav="usuarios",
            page_title="operadores — ventana.ia",
            kicker="OPERADORES",
            kicker_index="08",
            users=db.list_users(),
        ),
    )


@app.post("/usuarios")
@admin_required
async def usuarios_post(request: Request):
    form = await request.form()
    username = str(form.get("username") or "").strip().lower()
    password = str(form.get("password") or "")
    role = str(form.get("role") or "deposito")
    display = str(form.get("display_name") or username)
    if role not in {"deposito", "admin"}:
        role = "deposito"
    if not username or not password:
        flash(request, "Usuario y clave son obligatorios.", "advertencia")
        return RedirectResponse("/usuarios", status_code=303)
    if db.get_user_by_username(username):
        flash(request, "Ese usuario ya existe.", "advertencia")
        return RedirectResponse("/usuarios", status_code=303)
    db.create_user(username, hash_password(password), role, display)
    flash(request, "Operador activado.", "ok")
    return RedirectResponse("/usuarios", status_code=303)


@app.get("/foto/{name}")
@login_required
async def foto(name: str):
    path = UPLOAD_DIR / name
    if not path.exists() or not path.is_file():
        return RedirectResponse("/static/img/mark.svg", status_code=303)
    return FileResponse(path)


@app.get("/favicon.ico")
async def favicon():
    return FileResponse(ROOT / "static" / "img" / "favicon.svg", media_type="image/svg+xml")
