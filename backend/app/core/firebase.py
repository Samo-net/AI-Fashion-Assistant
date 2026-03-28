import firebase_admin
from firebase_admin import credentials, auth
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings

_firebase_app = None
_security = HTTPBearer()


_firebase_available = False


def init_firebase():
    global _firebase_app, _firebase_available
    import os
    if not firebase_admin._apps:
        cred_path = settings.FIREBASE_CREDENTIALS_PATH
        if not os.path.exists(cred_path):
            import logging
            logging.getLogger(__name__).warning(
                f"Firebase credentials not found at '{cred_path}'. "
                "Auth will return a dev stub. Add firebase-credentials.json to enable real auth."
            )
            _firebase_available = False
            return
        cred = credentials.Certificate(cred_path)
        _firebase_app = firebase_admin.initialize_app(cred)
        _firebase_available = True


async def verify_firebase_token(
    credentials: HTTPAuthorizationCredentials = Security(_security),
) -> dict:
    # Dev mode: credentials file missing — return a stub user so endpoints are testable
    if not _firebase_available:
        return {"uid": "dev-user-001", "email": "dev@fashionassistant.local"}

    token = credentials.credentials
    try:
        decoded = auth.verify_id_token(token)
        return decoded
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
