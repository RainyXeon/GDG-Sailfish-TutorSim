"""
BẢO MẬT: băm mật khẩu (PBKDF2-SHA256, có muối, thư viện chuẩn của Python) và JWT (PyJWT, HS256).
Không bao giờ lưu mật khẩu gốc; không bao giờ trả password_hash ra ngoài API.
"""
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

import jwt

from settings import settings

ITERATIONS = 200_000
ALGO = "HS256"


def hash_password(password):
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, ITERATIONS)
    return f"pbkdf2_sha256${ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password, stored):
    try:
        algo, iters, salt_hex, digest_hex = stored.split("$")
        if algo != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), int(iters))
        return hmac.compare_digest(digest.hex(), digest_hex)
    except (ValueError, TypeError):
        return False


def create_token(user):
    now = datetime.now(timezone.utc)
    payload = {"sub": str(user["id"]), "role": user["role"], "iat": now,
               "exp": now + timedelta(days=settings.jwt_expire_days)}
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGO)


def decode_token(token):
    """Trả về user_id (int) hoặc None nếu token sai / hết hạn."""
    try:
        data = jwt.decode(token, settings.jwt_secret, algorithms=[ALGO], options={"require": ["sub", "exp"]})
        return int(data["sub"])
    except (jwt.PyJWTError, ValueError, KeyError):
        return None
