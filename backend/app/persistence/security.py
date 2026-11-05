"""Password hashing and JWT token helpers (dependency-free).

Replaces the legacy ``passlib[bcrypt]`` + ``python-jose`` stack with stdlib
implementations so the persistence layer installs without native wheels:

* password hashing — PBKDF2-HMAC-SHA256 with a per-password salt;
* tokens — HS256 JWT built with ``hmac``/``base64``/``json``.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from typing import Any

_PBKDF2_ITERATIONS = 260_000


def hash_password(password: str) -> str:
    """Return a ``pbkdf2_sha256$iterations$salt$digest`` string."""
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _PBKDF2_ITERATIONS)
    return "pbkdf2_sha256${}${}${}".format(
        _PBKDF2_ITERATIONS,
        base64.b64encode(salt).decode("ascii"),
        base64.b64encode(digest).decode("ascii"),
    )


def verify_password(password: str, encoded: str) -> bool:
    """Constant-time verification of a stored ``pbkdf2_sha256`` hash."""
    try:
        scheme, iterations, salt_b64, digest_b64 = encoded.split("$")
        if scheme != "pbkdf2_sha256":
            return False
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(digest_b64)
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, int(iterations))
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def create_access_token(
    subject: str,
    secret_key: str,
    expires_minutes: int = 30,
    extra: dict[str, Any] | None = None,
) -> str:
    """Create an HS256 JWT with ``sub``, ``exp`` and ``iat`` claims."""
    now = int(time.time())
    header = {"alg": "HS256", "typ": "JWT"}
    payload: dict[str, Any] = {"sub": subject, "iat": now, "exp": now + expires_minutes * 60}
    if extra:
        payload.update(extra)

    signing_input = _b64url(json.dumps(header, separators=(",", ":")).encode()) + "." + _b64url(
        json.dumps(payload, separators=(",", ":")).encode()
    )
    signature = hmac.new(secret_key.encode("utf-8"), signing_input.encode("ascii"), hashlib.sha256).digest()
    return signing_input + "." + _b64url(signature)


def decode_token(token: str, secret_key: str) -> dict[str, Any]:
    """Decode and validate an HS256 JWT; raise ``ValueError`` on any failure."""
    try:
        signing_input, signature = token.rsplit(".", 1)
        expected = hmac.new(
            secret_key.encode("utf-8"), signing_input.encode("ascii"), hashlib.sha256
        ).digest()
        if not hmac.compare_digest(_b64url(expected), signature):
            raise ValueError("signature mismatch")
        header_b64, payload_b64 = signing_input.split(".")
        header = json.loads(_b64decode(header_b64))
        if header.get("alg") != "HS256":
            raise ValueError("unsupported algorithm")
        payload = json.loads(_b64decode(payload_b64))
    except (ValueError, json.JSONDecodeError) as exc:
        raise ValueError("malformed token") from exc

    if payload.get("exp", 0) < int(time.time()):
        raise ValueError("token expired")
    return payload


def _b64decode(data: str) -> bytes:
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))
