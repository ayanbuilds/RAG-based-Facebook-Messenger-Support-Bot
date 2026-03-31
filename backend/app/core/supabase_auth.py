import time
import requests
from jose import jwt
# from jose.utils import base64url_decode
from fastapi import HTTPException, Request

from app.core.config import settings

_JWKS_CACHE = {"keys": None, "ts": 0}
_JWKS_TTL = 3600  # seconds

def _get_jwks():
    now = time.time()
    if _JWKS_CACHE["keys"] and (now - _JWKS_CACHE["ts"] < _JWKS_TTL):
        return _JWKS_CACHE["keys"]

    url = f"{settings.SUPABASE_URL}/auth/v1/.well-known/jwks.json"
    
    try:
        r = requests.get(
            url, 
            headers={"apikey": settings.SUPABASE_ANON_KEY},
            timeout=10
        )
        
        if r.status_code >= 400:
            raise HTTPException(status_code=500, detail="Failed to fetch JWKS")

        data = r.json()
        
        _JWKS_CACHE["keys"] = data.get("keys", [])
        _JWKS_CACHE["ts"] = now
        return _JWKS_CACHE["keys"]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"JWKS error: {str(e)}")

def require_supabase_user(request: Request):
    auth = request.headers.get("authorization", "")
    
    if not auth.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")

    token = auth.split(" ", 1)[1].strip()

    try:
        header = jwt.get_unverified_header(token)
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token header")

    jwks = _get_jwks()
    
    key = next((k for k in jwks if k.get("kid") == header.get("kid")), None)
    if not key:
        raise HTTPException(status_code=401, detail="Signing key not found")
    try:
        payload = jwt.decode(
            token,
            key,
            algorithms=[header.get("alg", "RS256")],
            audience=settings.SUPABASE_JWT_AUD,
            issuer=f"{settings.SUPABASE_URL}/auth/v1",
        )
        return payload
    except Exception as e:
        raise HTTPException(status_code=401, detail="Token verification failed")