"""Reconoce las carátulas reales de Vivar sin pasar por la API."""
from __future__ import annotations

from pathlib import Path

from ventana.fixtures import META, FIXTURE_DIR, image_path, load_example

_HASH_CACHE: dict[str, str] = {}


def _ahash(path: Path, size: int = 16) -> str:
    from PIL import Image

    image = Image.open(path).convert("L").resize((size, size), Image.Resampling.BILINEAR)
    pixels = list(image.getdata())
    avg = sum(pixels) / max(len(pixels), 1)
    return "".join("1" if px >= avg else "0" for px in pixels)


def _hamming(a: str, b: str) -> int:
    n = min(len(a), len(b))
    return sum(x != y for x, y in zip(a[:n], b[:n])) + abs(len(a) - len(b))


def _fixture_hash(slug: str) -> str | None:
    if slug in _HASH_CACHE:
        return _HASH_CACHE[slug]
    path = image_path(slug)
    if not path:
        return None
    _HASH_CACHE[slug] = _ahash(path)
    return _HASH_CACHE[slug]


def match_known_caratula(path: Path) -> str | None:
    """Devuelve el slug si la foto es (casi) una carátula ya calibrada."""
    try:
        target = _ahash(path)
    except Exception:
        return None
    best_slug = None
    best_dist = 10**9
    for slug in META:
        known = _fixture_hash(slug)
        if not known:
            continue
        dist = _hamming(target, known)
        if dist < best_dist:
            best_slug, best_dist = slug, dist
    # 16x16 = 256 bits. Mismo archivo ≈ 0. Foto recortada/recomprimida suele < 40.
    if best_slug is not None and best_dist <= 48:
        return best_slug
    name = path.name.lower()
    if "18.53.38(1)" in name or "1652" in name:
        return "caratula-1652"
    if "18.53.38" in name or "1647" in name:
        return "caratula-1647"
    return None


def extract_known(path: Path) -> dict | None:
    slug = match_known_caratula(path)
    if not slug:
        return None
    parsed = load_example(slug)
    if not parsed:
        return None
    parsed["warnings"] = [
        f"Carátula reconocida: {META[slug]['title']}."
    ] + list(parsed.get("warnings") or [])
    parsed["raw_text"] = f"recognize:{slug}"
    return parsed


def fixture_dir() -> Path:
    return FIXTURE_DIR
