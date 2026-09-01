ALTER TABLE categorias
ADD CONSTRAINT uq_categoria_nome
UNIQUE (nome);

ALTER TABLE produtos
ADD CONSTRAINT uq_produto_nome
UNIQUE (nome);

ALTER TABLE produtos
ALTER COLUMN estoque SET DEFAULT 0;

ALTER TABLE produtos
ADD CONSTRAINT chk_produto_nome
CHECK (LENGTH(TRIM(nome)) >= 2);