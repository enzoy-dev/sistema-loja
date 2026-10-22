from fastapi.testclient import TestClient

from api.main import app


def test_real_connection_uses_pgdatabase(connection, test_database, monkeypatch):
    from conftest import TEST_PASSWORD, TEST_PASSWORD_HASH

    connection.execute(
        "INSERT INTO usuarios_api (login, senha_hash, perfil) VALUES ('conexao-admin',%s,'admin')",
        (TEST_PASSWORD_HASH,),
    )
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("PGDATABASE", test_database)
    with TestClient(app) as client:
        assert client.get("/health").json() == {"status": "ok"}
        token = client.post(
            "/auth/login", json={"login": "conexao-admin", "senha": TEST_PASSWORD}
        ).json()["access_token"]
        client.headers["Authorization"] = "Bearer " + token
        response = client.post("/categorias", json={"nome": "Conexão real"})
        assert response.status_code == 201
    assert (
        connection.execute(
            "SELECT count(*) AS n FROM categorias WHERE nome='Conexão real'"
        ).fetchone()["n"]
        == 1
    )


def test_database_url_takes_precedence(connection, test_database, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "dbname=" + test_database)
    monkeypatch.setenv("PGDATABASE", "banco_que_nao_existe")
    with TestClient(app) as client:
        assert client.get("/health").status_code == 200


def test_connection_failure_is_reported_without_details(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("PGDATABASE", "banco_que_nao_existe")
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 503
    assert response.json() == {"detail": "Banco de dados indisponível"}
