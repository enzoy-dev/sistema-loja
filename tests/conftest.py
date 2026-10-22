"""Integração real: cria e remove somente um banco temporário exclusivo dos testes."""

import os
from pathlib import Path
import subprocess
import uuid

import psycopg
from psycopg import sql
from psycopg.rows import dict_row
import pytest
from fastapi.testclient import TestClient

from api.db import get_connection
from api.main import app
from api.auth import hash_password

ROOT = Path(__file__).resolve().parents[1]
TEST_PASSWORD = "local-test-password-only"
TEST_PASSWORD_HASH = hash_password(TEST_PASSWORD)


@pytest.fixture(scope="session")
def test_database():
    name = "loja_api_teste_" + uuid.uuid4().hex[:12]
    with psycopg.connect(
        dbname=os.getenv("PGDATABASE", "postgres"), autocommit=True
    ) as admin:
        admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
        try:
            yield name
        finally:
            admin.execute(
                sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(name))
            )


@pytest.fixture
def connection(test_database):
    # Este schema pertence exclusivamente ao banco temporário criado acima.
    with psycopg.connect(dbname=test_database, autocommit=True) as reset:
        reset.execute("DROP SCHEMA public CASCADE; CREATE SCHEMA public")
    subprocess.run(
        [
            "psql",
            "-X",
            "-v",
            "ON_ERROR_STOP=1",
            "-d",
            test_database,
            "-f",
            str(ROOT / "sql/00_setup.sql"),
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    with psycopg.connect(
        dbname=test_database, autocommit=True, row_factory=dict_row
    ) as conn:
        yield conn


@pytest.fixture
def raw_client(connection, test_database):
    def override_connection():
        with psycopg.connect(dbname=test_database, row_factory=dict_row) as conn:
            yield conn

    app.dependency_overrides[get_connection] = override_connection
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def client(raw_client, connection):
    connection.execute(
        "INSERT INTO usuarios_api (login, senha_hash, perfil) VALUES (%s,%s,%s)",
        ("admin-teste", TEST_PASSWORD_HASH, "admin"),
    )
    response = raw_client.post(
        "/auth/login", json={"login": "admin-teste", "senha": TEST_PASSWORD}
    )
    assert response.status_code == 200, response.text
    raw_client.headers["Authorization"] = "Bearer " + response.json()["access_token"]
    return raw_client
