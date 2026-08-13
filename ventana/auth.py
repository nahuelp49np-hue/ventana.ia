from __future__ import annotations

import hashlib
import inspect
import secrets
from functools import wraps
from typing import Any, Callable

from fastapi import Request
from fastapi.responses import RedirectResponse

ITERATIONS = 200_000


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), ITERATIONS
    )
    return f"pbkdf2${salt}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        kind, salt, hexhash = stored.split("$", 2)
    except ValueError:
        return False
    if kind != "pbkdf2":
        return False
    dk = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), ITERATIONS
    )
    return secrets.compare_digest(dk.hex(), hexhash)


def current_user(request: Request) -> dict[str, Any] | None:
    return request.session.get("user")


def _request_from(args, kwargs) -> Request | None:
    req = kwargs.get("request")
    if isinstance(req, Request):
        return req
    for value in args:
        if isinstance(value, Request):
            return value
    return None


def login_required(fn: Callable):
    @wraps(fn)
    async def wrapper(*args, **kwargs):
        request = _request_from(args, kwargs)
        if not request or not current_user(request):
            return RedirectResponse("/acceso", status_code=303)
        return await fn(*args, **kwargs)

    wrapper.__signature__ = inspect.signature(fn)
    return wrapper


def admin_required(fn: Callable):
    @wraps(fn)
    async def wrapper(*args, **kwargs):
        request = _request_from(args, kwargs)
        user = current_user(request) if request else None
        if not user:
            return RedirectResponse("/acceso", status_code=303)
        if user.get("role") != "admin":
            return RedirectResponse("/control", status_code=303)
        return await fn(*args, **kwargs)

    wrapper.__signature__ = inspect.signature(fn)
    return wrapper
