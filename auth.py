
import os
import uuid

from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash


# =====================================================
# JWT CONFIGURATION
# =====================================================

SECRET_KEY = os.getenv("CHESS_SECRET_KEY")

if not SECRET_KEY:
    raise RuntimeError(
        "CHESS_SECRET_KEY environment variable is not set."
    )

ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24


# =====================================================
# PASSWORD HASHING
# =====================================================

password_hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """Securely hash a user's password using Argon2."""
    return password_hasher.hash(password)


def verify_password(
    password: str,
    hashed_password: str
) -> bool:
    """Verify a password against its stored hash."""
    return password_hasher.verify(
        password,
        hashed_password
    )


# =====================================================
# JWT TOKEN CREATION
# =====================================================

def create_access_token(user_id: int) -> str:
    """Create a JWT access token for a user."""

    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(user_id),
        "jti": str(uuid.uuid4()),
        "iat": datetime.now(timezone.utc),
        "exp": expires_at,
    }

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )


# =====================================================
# JWT TOKEN DECODING
# =====================================================

def decode_access_token(token: str) -> dict:
    """Decode and validate a JWT access token."""

    payload = jwt.decode(
        token,
        SECRET_KEY,
        algorithms=[ALGORITHM],
    )

    user_id = payload.get("sub")
    token_id = payload.get("jti")
    expiration = payload.get("exp")

    if not user_id or not token_id or not expiration:
        raise ValueError("Invalid token payload")

    return {
        "user_id": int(user_id),
        "jti": token_id,
        "expires_at": datetime.fromtimestamp(
            expiration,
            tz=timezone.utc
        ).replace(tzinfo=None),
    }


# =====================================================
# TOKEN EXPIRATION HELPER
# =====================================================

def is_token_expired(token_data: dict) -> bool:
    """Check whether a decoded token has expired."""

    return datetime.utcnow() >= token_data["expires_at"]
