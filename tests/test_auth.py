from datetime import datetime, timezone

import pytest

from api.auth import hash_password, token_digest, verify_password
from conftest import TEST_PASSWORD, TEST_PASSWORD_HASH


def account(connection, role="admin", login="equipe-teste"):
    return connection.execute(
        """INSERT INTO usuarios_api (login, senha_hash, perfil)
        VALUES (%s,%s,%s) RETURNING id""",
        (login, TEST_PASSWORD_HASH, role),
    ).fetchone()["id"]


def login(client, name="equipe-teste", password=TEST_PASSWORD):
    return client.post("/auth/login", json={"login": name, "senha": password})


def authorize(client):
    response = login(client)
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    client.headers["Authorization"] = "Bearer " + token
    return token


@pytest.mark.parametrize(
    "method,path,body",
    [
        ("get", "/categorias", None),
        ("post", "/categorias", {"nome": "nova"}),
        ("get", "/clientes", None),
        ("post", "/clientes", {"nome": "Nova", "email": "x@example.com"}),
        ("get", "/produtos", None),
        ("get", "/produtos/1", None),
        ("post", "/produtos", {"nome": "Novo", "preco": "10", "categoria_id": 1}),
        ("post", "/produtos/1/entradas", {"quantidade": 1}),
        ("get", "/pedidos", None),
        ("get", "/pedidos/1", None),
        (
            "post",
            "/pedidos",
            {"cliente_id": 1, "itens": [{"produto_id": 1, "quantidade": 1}]},
        ),
        ("post", "/pedidos/1/cancelar", None),
        ("get", "/auth/me", None),
        ("get", "/auth/usuarios", None),
        ("post", "/auth/logout", None),
    ],
)
def test_business_routes_require_authentication(raw_client, method, path, body):
    response = raw_client.request(method, path, json=body)
    assert response.status_code == 401, response.text
    assert response.headers["www-authenticate"] == "Bearer"


def test_tokens_are_hashed_expire_and_can_be_revoked(raw_client, connection):
    user = account(connection)
    token = authorize(raw_client)
    session = connection.execute("SELECT * FROM sessoes_api").fetchone()
    assert session["token_hash"] == token_digest(token) and token not in repr(session)
    assert session["expira_em"] > datetime.now(timezone.utc)
    assert raw_client.get("/auth/me").json() == {
        "id": user,
        "login": "equipe-teste",
        "perfil": "admin",
        "ativo": True,
    }
    assert raw_client.post("/auth/logout").status_code == 204
    assert raw_client.get("/produtos").status_code == 401
    token = authorize(raw_client)
    connection.execute(
        "UPDATE sessoes_api SET expira_em=clock_timestamp()-interval '1 second'"
    )
    assert raw_client.get("/produtos").status_code == 401


@pytest.mark.parametrize("role", ["leitor", "vendedor"])
def test_roles_cannot_change_catalog_stock_or_other_users(raw_client, connection, role):
    account(connection, role)
    authorize(raw_client)
    before = connection.execute("SELECT estoque FROM produtos WHERE id=1").fetchone()
    assert raw_client.get("/clientes").status_code == 200
    assert raw_client.get("/produtos").status_code == 200
    assert (
        raw_client.post("/produtos/1/entradas", json={"quantidade": 99}).status_code
        == 403
    )
    assert raw_client.post("/categorias", json={"nome": "Categoria"}).status_code == 403
    assert (
        raw_client.post(
            "/produtos", json={"nome": "Novo", "preco": "10", "categoria_id": 1}
        ).status_code
        == 403
    )
    assert raw_client.post("/pedidos/1/cancelar").status_code == 403
    assert (
        raw_client.post(
            "/auth/usuarios",
            json={"login": "invasor", "senha": TEST_PASSWORD, "perfil": "admin"},
        ).status_code
        == 403
    )
    assert (
        connection.execute("SELECT estoque FROM produtos WHERE id=1").fetchone()
        == before
    )
    payload = {"cliente_id": 1, "itens": [{"produto_id": 2, "quantidade": 1}]}
    response = raw_client.post("/pedidos", json=payload)
    assert response.status_code == (201 if role == "vendedor" else 403)
    customer = raw_client.post(
        "/clientes", json={"nome": "Nova Pessoa", "email": "nova@example.com"}
    )
    assert customer.status_code == (201 if role == "vendedor" else 403)


def test_admin_creates_users_and_changes_permissions_immediately(client, connection):
    created = client.post(
        "/auth/usuarios",
        json={"login": "novo-vendedor", "senha": TEST_PASSWORD, "perfil": "vendedor"},
    )
    assert created.status_code == 201
    assert "senha" not in created.text and "hash" not in created.text
    user_id = created.json()["id"]
    token = login(client, "novo-vendedor").json()["access_token"]
    headers = {"Authorization": "Bearer " + token}
    assert client.get("/auth/me", headers=headers).json()["perfil"] == "vendedor"
    assert (
        client.patch(
            f"/auth/usuarios/{user_id}", json={"perfil": "leitor", "ativo": True}
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/pedidos",
            json={"cliente_id": 1, "itens": [{"produto_id": 2, "quantidade": 1}]},
            headers=headers,
        ).status_code
        == 403
    )
    assert (
        client.patch(
            f"/auth/usuarios/{user_id}", json={"perfil": "leitor", "ativo": False}
        ).status_code
        == 200
    )
    assert client.get("/produtos", headers=headers).status_code == 401
    assert login(client, "novo-vendedor").status_code == 401
    assert (
        connection.execute(
            "SELECT count(*) AS n FROM sessoes_api WHERE usuario_id=%s", (user_id,)
        ).fetchone()["n"]
        == 0
    )
    own = client.get("/auth/me").json()["id"]
    assert (
        client.patch(
            f"/auth/usuarios/{own}", json={"perfil": "leitor", "ativo": False}
        ).status_code
        == 409
    )


@pytest.mark.parametrize("known", [True, False])
def test_failed_login_is_generic_and_limit_persists(raw_client, connection, known):
    if known:
        account(connection)
    for _ in range(5):
        response = login(raw_client, password="wrong-password")
        assert response.status_code == 401
        assert response.json()["detail"] == "Login ou senha inválidos"
    assert login(raw_client).status_code == 429
    assert (
        connection.execute("SELECT falhas FROM tentativas_login_api").fetchone()[
            "falhas"
        ]
        == 5
    )
    connection.execute(
        "UPDATE tentativas_login_api SET janela=clock_timestamp()-interval '16 minutes'"
    )
    assert login(raw_client).status_code == (200 if known else 401)


def test_password_hashes_are_salted_and_tampered_tokens_fail(raw_client, connection):
    encoded = hash_password(TEST_PASSWORD)
    assert encoded != TEST_PASSWORD_HASH
    assert verify_password(TEST_PASSWORD, encoded)
    assert not verify_password("wrong-password", encoded)
    assert not verify_password(TEST_PASSWORD, "malformed")
    account(connection)
    token = authorize(raw_client)
    forged = ("a" if token[0] != "a" else "b") + token[1:]
    assert (
        raw_client.get(
            "/clientes", headers={"Authorization": "Bearer " + forged}
        ).status_code
        == 401
    )
    assert raw_client.get("/health").status_code == 200


def test_auth_migration_preserves_existing_orders(connection):
    from conftest import ROOT

    original = connection.execute("SELECT * FROM pedidos ORDER BY id").fetchall()
    connection.execute("DROP TABLE tentativas_login_api, sessoes_api, usuarios_api")
    import subprocess

    subprocess.run(
        [
            "psql",
            "-X",
            "-v",
            "ON_ERROR_STOP=1",
            "-d",
            connection.info.dbname,
            "-f",
            str(ROOT / "migrations/002_autenticacao.sql"),
        ],
        check=True,
        capture_output=True,
    )
    assert (
        connection.execute("SELECT * FROM pedidos ORDER BY id").fetchall() == original
    )
    assert (
        connection.execute("SELECT count(*) AS n FROM usuarios_api").fetchone()["n"]
        == 0
    )


@pytest.mark.parametrize("value", ["0", "1441", "invalid"])
def test_invalid_session_duration_fails_without_creating_token(
    raw_client, connection, monkeypatch, value
):
    account(connection)
    monkeypatch.setenv("LOJA_SESSION_TTL_MINUTES", value)
    assert login(raw_client).status_code == 503
    assert (
        connection.execute("SELECT count(*) AS n FROM sessoes_api").fetchone()["n"] == 0
    )


def test_password_reset_cli_revokes_sessions(
    raw_client, connection, monkeypatch, capsys
):
    import psycopg
    from psycopg.rows import dict_row
    from api import manage

    account(connection)
    authorize(raw_client)
    password = "new-password-for-tests"
    monkeypatch.setattr(
        manage,
        "connect_database",
        lambda: psycopg.connect(dbname=connection.info.dbname, row_factory=dict_row),
    )
    monkeypatch.setattr(manage, "getpass", lambda prompt: password)
    monkeypatch.setattr(
        "sys.argv", ["manage", "reset-password", "--login", "equipe-teste"]
    )
    manage.main()
    assert password not in capsys.readouterr().out
    assert raw_client.get("/auth/me").status_code == 401
    assert login(raw_client, password=password).status_code == 200
    assert login(raw_client).status_code == 401


def test_concurrent_admin_demotion_cannot_remove_both_admins(raw_client, connection):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from fastapi import Depends
    from api.auth import current_user, read_bearer
    from api.db import get_connection
    from api.main import app

    a = account(connection, login="admin-a")
    b = account(connection, login="admin-b")
    tokens = {
        name: login(raw_client, name).json()["access_token"]
        for name in ["admin-a", "admin-b"]
    }
    barrier = Barrier(2)

    def synchronized_user(token=Depends(read_bearer), conn=Depends(get_connection)):
        user = current_user(token, conn)
        barrier.wait(timeout=10)
        return user

    app.dependency_overrides[current_user] = synchronized_user

    def demote(args):
        name, target = args
        return raw_client.patch(
            f"/auth/usuarios/{target}",
            headers={"Authorization": "Bearer " + tokens[name]},
            json={"perfil": "leitor", "ativo": True},
        ).status_code

    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            codes = list(pool.map(demote, [("admin-a", b), ("admin-b", a)]))
    finally:
        app.dependency_overrides.pop(current_user, None)
    assert sorted(codes) == [200, 403]
    assert (
        connection.execute(
            "SELECT count(*) AS n FROM usuarios_api WHERE perfil='admin' AND ativo"
        ).fetchone()["n"]
        == 1
    )
