"""Firebase ID token validation (optional in development)."""

from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorization, HTTPBearer

from app.core.config import get_settings

security = HTTPBearer(auto_error=False)
settings = get_settings()

_firebase_app = None


def _init_firebase():
    global _firebase_app
    if _firebase_app is not None or not settings.firebase_configured:
        return _firebase_app
    try:
        import firebase_admin
        from firebase_admin import credentials

        private_key = settings.firebase_private_key.replace("\\n", "\n")
        cred = credentials.Certificate(
            {
                "type": "service_account",
                "project_id": settings.firebase_project_id,
                "private_key": private_key,
                "client_email": settings.firebase_client_email,
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        )
        _firebase_app = firebase_admin.initialize_app(cred)
    except Exception:
        _firebase_app = None
    return _firebase_app


def verify_firebase_token(token: str) -> Optional[dict]:
    """Verify Firebase ID token; returns decoded claims or None."""
    if not settings.firebase_configured:
        return {"uid": "dev-user", "email": "dev@enertwin.local"}

    _init_firebase()
    try:
        from firebase_admin import auth

        return auth.verify_id_token(token)
    except Exception:
        return None


async def get_current_user(
    credentials: Optional[HTTPAuthorization] = Depends(security),
) -> Optional[dict]:
    """
    Optional auth dependency.
    When Firebase is not configured, allows unauthenticated access for demo.
    When configured, requires valid Bearer token.
    """
    if not settings.firebase_configured:
        return {"uid": "dev-user", "email": "dev@enertwin.local"}

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"success": False, "error": "Missing authentication token", "code": "UNAUTHORIZED"},
        )

    user = verify_firebase_token(credentials.credentials)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"success": False, "error": "Invalid authentication token", "code": "INVALID_TOKEN"},
        )
    return user
