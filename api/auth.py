"""Database-backed bearer sessions for internal staff, without default accounts."""

from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import os
import re
import secrets
from typing import Annotated, Literal

import psycopg
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, Field, SecretStr

from api.db import get_connection

ITERATIONS = 600_000
_DUMMY_HASH = hashlib.pbkdf2_hmac(
    "sha256", b"not-a-user-password", b"fixed-dummy-salt", ITERATIONS
).hex()
Connection = Annotated[psycopg.Connection, Depends(get_connection)]
Role = Literal["admin", "vendedor", "leitor"]
Login = Annotated[str, Field(pattern=r"^[a-z0-9._-]{3,64}$")]
bearer = HTTPBearer(auto_error=False)
router = APIRouter(prefix="/auth", tags=["Autenticação"])


def hash_password(password):
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), bytes.fromhex(salt), ITERATIONS
    )
    return f"pbkdf2_sha256${ITERATIONS}${salt}${digest.hex()}"


def verify_password(password, encoded):
    try:
        algorithm, iterations, salt, expected = encoded.split("$")
        if algorithm != "pbkdf2_sha256" or int(iterations) != ITERATIONS:
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), bytes.fromhex(salt), int(iterations)
        )
        return hmac.compare_digest(digest.hex(), expected)
    except (ValueError, TypeError):
        return False


def token_digest(token):
    return hashlib.sha256(token.encode()).hexdigest()


def read_bearer(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
):
    if credentials is None or not 32 <= len(credentials.credentials) <= 128:
        raise HTTPException(
            401, "Autenticação necessária", headers={"WWW-Authenticate": "Bearer"}
        )
    return credentials.credentials


def current_user(token: Annotated[str, Depends(read_bearer)], connection: Connection):
    user = connection.execute(
        """
        SELECT u.id, u.login, u.perfil, u.ativo FROM usuarios_api u
        JOIN sessoes_api s ON s.usuario_id=u.id
        WHERE s.token_hash=%s AND s.expira_em > clock_timestamp() AND u.ativo
    """,
        (token_digest(token),),
    ).fetchone()
    if user is None:
        raise HTTPException(
            401, "Sessão inválida ou expirada", headers={"WWW-Authenticate": "Bearer"}
        )
    return user


def require_roles(*roles):
    def permitted(user: Annotated[dict, Depends(current_user)]):
        if user["perfil"] not in roles:
            raise HTTPException(403, "Seu perfil não permite esta operação")
        return user

    return permitted


class LoginInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    login: Login
    senha: SecretStr = Field(min_length=1, max_length=128)


class UserInput(LoginInput):
    senha: SecretStr = Field(min_length=12, max_length=128)
    perfil: Role = "leitor"


class UserUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    perfil: Role
    ativo: bool = Field(strict=True)


def create_user(connection, login, password, role):
    if (
        not re.fullmatch(r"[a-z0-9._-]{3,64}", login)
        or role not in {"admin", "vendedor", "leitor"}
        or not 12 <= len(password) <= 128
    ):
        raise ValueError(
            "Login, senha ou perfil inválido; use senha entre 12 e 128 caracteres"
        )
    return connection.execute(
        """INSERT INTO usuarios_api (login, senha_hash, perfil)
        VALUES (%s, %s, %s) RETURNING id, login, perfil, ativo, criado_em""",
        (login, hash_password(password), role),
    ).fetchone()


@router.post("/login")
def login(body: LoginInput, connection: Connection):
    try:
        ttl = int(os.getenv("LOJA_SESSION_TTL_MINUTES", "60"))
    except ValueError:
        raise HTTPException(503, "Tempo de sessão configurado incorretamente")
    if not 1 <= ttl <= 1440:
        raise HTTPException(503, "Tempo de sessão configurado incorretamente")
    connection.execute(
        "DELETE FROM tentativas_login_api WHERE janela < clock_timestamp() - interval '1 day'"
    )
    connection.execute(
        "INSERT INTO tentativas_login_api (login) VALUES (%s) ON CONFLICT DO NOTHING",
        (body.login,),
    )
    attempt = connection.execute(
        """SELECT falhas, janela > clock_timestamp() - interval '15 minutes' AS recente
        FROM tentativas_login_api WHERE login=%s FOR UPDATE""",
        (body.login,),
    ).fetchone()
    if attempt["recente"] and attempt["falhas"] >= 5:
        return JSONResponse(
            status_code=429,
            content={"detail": "Muitas tentativas. Aguarde 15 minutos."},
            headers={"Retry-After": "900"},
        )
    user = connection.execute(
        "SELECT * FROM usuarios_api WHERE login=%s", (body.login,)
    ).fetchone()
    encoded = (
        user["senha_hash"]
        if user
        else f"pbkdf2_sha256${ITERATIONS}$66697865642d64756d6d792d73616c74${_DUMMY_HASH}"
    )
    valid = verify_password(body.senha.get_secret_value(), encoded)
    if not valid or not user or not user["ativo"]:
        connection.execute(
            """UPDATE tentativas_login_api SET
            falhas=CASE WHEN %s THEN falhas+1 ELSE 1 END,
            janela=CASE WHEN %s THEN janela ELSE clock_timestamp() END WHERE login=%s""",
            (attempt["recente"], attempt["recente"], body.login),
        )
        # Return a response, rather than raise: commit the failed-attempt counter.
        return JSONResponse(
            status_code=401,
            content={"detail": "Login ou senha inválidos"},
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = secrets.token_urlsafe(32)
    expires = datetime.now(timezone.utc) + timedelta(minutes=ttl)
    connection.execute("DELETE FROM sessoes_api WHERE expira_em <= clock_timestamp()")
    connection.execute(
        "INSERT INTO sessoes_api (token_hash, usuario_id, expira_em) VALUES (%s,%s,%s)",
        (token_digest(token), user["id"], expires),
    )
    connection.execute("DELETE FROM tentativas_login_api WHERE login=%s", (body.login,))
    return {"access_token": token, "token_type": "bearer", "expires_at": expires}


@router.get("/me")
def me(user: Annotated[dict, Depends(current_user)]):
    return user


@router.post("/logout", status_code=204)
def logout(
    user: Annotated[dict, Depends(current_user)],
    token: Annotated[str, Depends(read_bearer)],
    connection: Connection,
):
    connection.execute(
        "DELETE FROM sessoes_api WHERE token_hash=%s", (token_digest(token),)
    )


@router.post(
    "/usuarios", status_code=201, dependencies=[Depends(require_roles("admin"))]
)
def add_user(body: UserInput, connection: Connection):
    return create_user(
        connection, body.login, body.senha.get_secret_value(), body.perfil
    )


@router.get("/usuarios", dependencies=[Depends(require_roles("admin"))])
def list_users(connection: Connection):
    return connection.execute(
        "SELECT id, login, perfil, ativo, criado_em FROM usuarios_api ORDER BY id"
    ).fetchall()


@router.patch("/usuarios/{user_id}", dependencies=[Depends(require_roles("admin"))])
def update_user(
    user_id: int,
    body: UserUpdate,
    user: Annotated[dict, Depends(current_user)],
    connection: Connection,
):
    if user_id == user["id"]:
        raise HTTPException(409, "Não altere o próprio perfil ou acesso nesta rota")
    # Serialize role changes and recheck the actor after waiting. Two admins
    # cannot simultaneously demote each other and leave the store without one.
    connection.execute("SELECT pg_advisory_xact_lock(724102)")
    actor = connection.execute(
        "SELECT perfil, ativo FROM usuarios_api WHERE id=%s", (user["id"],)
    ).fetchone()
    if not actor or not actor["ativo"] or actor["perfil"] != "admin":
        raise HTTPException(403, "Seu perfil não permite esta operação")
    updated = connection.execute(
        """UPDATE usuarios_api SET perfil=%s, ativo=%s WHERE id=%s
        RETURNING id, login, perfil, ativo, criado_em""",
        (body.perfil, body.ativo, user_id),
    ).fetchone()
    if updated is None:
        raise HTTPException(404, "Usuário não encontrado")
    if not body.ativo:
        connection.execute("DELETE FROM sessoes_api WHERE usuario_id=%s", (user_id,))
    return updated
