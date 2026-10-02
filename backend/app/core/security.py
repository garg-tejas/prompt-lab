import time

from fastapi import HTTPException, status
from jwt import InvalidTokenError, PyJWKClient
from jwt import decode as jwt_decode

from app.config import get_settings

settings = get_settings()

_jwks_client: PyJWKClient | None = None
_jwks_loaded_at: float = 0.0
_JWKS_TTL_SECONDS = 3600


def _jwks() -> PyJWKClient:
    global _jwks_client, _jwks_loaded_at
    now = time.time()
    if _jwks_client is None or now - _jwks_loaded_at > _JWKS_TTL_SECONDS:
        if not settings.clerk_jwt_issuer:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Clerk issuer is not configured",
            )
        _jwks_client = PyJWKClient(
            f"{settings.clerk_jwt_issuer}/.well-known/jwks.json",
            cache_keys=True,
            lifespan=_JWKS_TTL_SECONDS,
        )
        _jwks_loaded_at = now
    return _jwks_client


def verify_clerk_token(token: str) -> dict:
    """Verify a Clerk JWT and return its payload. JWKS keys refresh hourly."""
    try:
        signing_key = _jwks().get_signing_key_from_jwt(token)
        return jwt_decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            issuer=settings.clerk_jwt_issuer,
            options={"require": ["exp", "iss", "sub"]},
        )
    except HTTPException:
        raise
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
        ) from exc
