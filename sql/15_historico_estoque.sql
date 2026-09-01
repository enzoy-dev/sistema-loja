CREATE TABLE movimentacoes_estoque (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    produto_id INTEGER NOT NULL,
    tipo VARCHAR(20) NOT NULL,
    quantidade INTEGER NOT NULL,
    data_movimentacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_movimentacao_produto
        FOREIGN KEY (produto_id)
        REFERENCES produtos(id),

    CONSTRAINT chk_movimentacao_tipo
        CHECK (tipo IN ('entrada', 'saida')),

    CONSTRAINT chk_movimentacao_quantidade
        CHECK (quantidade > 0)
);