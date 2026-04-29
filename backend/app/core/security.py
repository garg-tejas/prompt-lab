import httpx
from jose import jwt, jwk
from jose.exceptions import JWTError
from fastapi import HTTPException, status
from functools import lru_cache

from app.config import get_settings

settings = get_settings()


@lru_cache
def get_clerk_jwks() -> dict:
    jwks_url = f"{settings.clerk_jwt_issuer}/.well-known/jwks.json"
    response = httpx.get(jwks_url, timeout=10.0)
    response.raise_for_status()
    return response.json()


def verify_clerk_token(token: str) -> dict:
    """Verify a Clerk JWT token and return its payload."""
    try:
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")
        if not kid:
            raise ValueError("No 'kid' found in token header")

        jwks = get_clerk_jwks()
        key_data = None
        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                key_data = key
                break

        if not key_data:
            raise ValueError("No matching JWKS key found")

        public_key = jwk.construct(key_data)
        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            issuer=settings.clerk_jwt_issuer,
            options={"require": ["exp", "iss", "sub"]},
        )
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication credentials: {e}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication error: {e}",
        )
