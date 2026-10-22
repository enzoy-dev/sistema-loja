-- Contas internas da equipe; independentes dos clientes comerciais.
CREATE TABLE usuarios_api (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    login VARCHAR(64) NOT NULL UNIQUE CHECK (login ~ '^[a-z0-9._-]{3,64}$'),
    senha_hash TEXT NOT NULL,
    perfil TEXT NOT NULL CHECK (perfil IN ('admin', 'vendedor', 'leitor')),
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

CREATE TABLE sessoes_api (
    token_hash CHAR(64) PRIMARY KEY,
    usuario_id INTEGER NOT NULL REFERENCES usuarios_api(id) ON DELETE CASCADE,
    expira_em TIMESTAMPTZ NOT NULL,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);
CREATE INDEX sessoes_api_usuario ON sessoes_api(usuario_id);
CREATE INDEX sessoes_api_expiracao ON sessoes_api(expira_em);

CREATE TABLE tentativas_login_api (
    login VARCHAR(64) PRIMARY KEY,
    falhas INTEGER NOT NULL DEFAULT 0 CHECK (falhas >= 0),
    janela TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);
