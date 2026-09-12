""" Autenticación de Muuk. 

Responsabilidades: 
- Validar credenciales del usuario. 
- Generar un JWT.
- Recuperar el user_id desde un JWT válido. 
- Proporcionar una dependencia de FastAPI para proteger endpoints. 

No realiza consultas de negocio ni accede directamente a transacciones. 
"""
import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel


# ============================================================
# CONFIGURACIÓN
# ============================================================

JWT_SECRET = os.getenv(
    "JWT_SECRET",
    "muuk-dev-secret-change-in-production"
)

JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_MINUTES = 60


# ============================================================
# SEGURIDAD HTTP
# ============================================================

bearer_scheme = HTTPBearer()


# ============================================================
# MODELOS
# ============================================================

class LoginRequest(BaseModel):
    user_id: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str


# ============================================================
# CREDENCIALES DEMO
# ============================================================

# Usuarios temporales para el hack.
#
# En producción estas credenciales NO deben estar aquí:
# deben validarse contra un sistema de identidad/base de datos
# usando contraseñas almacenadas como hashes.

DEMO_USERS = {
    "u1": os.getenv("MUUK_USER_U1_PASSWORD", "demo123"),
    "u2": os.getenv("MUUK_USER_U2_PASSWORD", "demo123"),
}


# ============================================================
# LOGIN
# ============================================================

def authenticate_user(user_id: str, password: str) -> bool:
    """
    Valida las credenciales del usuario.

    Retorna True si las credenciales son válidas.
    """

    expected_password = DEMO_USERS.get(user_id)

    if expected_password is None:
        return False

    return password == expected_password


def create_access_token(user_id: str) -> str:
    """
    Genera un JWT para el usuario autenticado.
    """

    expiration = datetime.now(timezone.utc) + timedelta(
        minutes=JWT_EXPIRATION_MINUTES
    )

    payload = {
        "sub": user_id,
        "exp": expiration,
    }

    return jwt.encode(
        payload,
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )


def login(user_id: str, password: str) -> LoginResponse:
    """
    Autentica al usuario y devuelve un JWT.
    """

    if not authenticate_user(user_id, password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas.",
        )

    token = create_access_token(user_id)

    return LoginResponse(
        access_token=token,
        user_id=user_id,
    )


# ============================================================
# JWT VALIDATION
# ============================================================

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> str:
    """
    Dependencia de FastAPI.

    Lee:

        Authorization: Bearer <token>

    y devuelve el user_id almacenado en el JWT.
    """

    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
        )

        user_id = payload.get("sub")

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido.",
            )

        return str(user_id)

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="El token ha expirado.",
        )

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido.",
        )