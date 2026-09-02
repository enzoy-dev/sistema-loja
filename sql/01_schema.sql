CREATE TABLE categorias (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nome VARCHAR(100) NOT NULL
);

CREATE TABLE clientes (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL,
    telefone VARCHAR(20),
    data_cadastro DATE NOT NULL DEFAULT CURRENT_DATE,

    CONSTRAINT uq_cliente_email
        UNIQUE (email),

    CONSTRAINT chk_cliente_nome
        CHECK (LENGTH(TRIM(nome)) >= 3),

    CONSTRAINT chk_cliente_email
        CHECK (POSITION('@' IN email) > 1)
);


CREATE TABLE produtos (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nome VARCHAR(150) NOT NULL,
    preco DECIMAL(10,2) CHECK (preco >= 0) NOT NULL,
    estoque INTEGER NOT NULL,
    categoria_id INTEGER NOT NULL
);

CREATE TABLE pedidos (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    cliente_id INTEGER NOT NULL,
    data_pedido DATE NOT NULL DEFAULT CURRENT_DATE,
    status VARCHAR(30) NOT NULL
);

CREATE TABLE itens_pedido (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
pedido_id INTEGER NOT NULL,
    produto_id INTEGER NOT NULL,
    quantidade INTEGER NOT NULL,
    preco_unitario DECIMAL(10,2) NOT NULL
);

ALTER TABLE produtos
ADD CONSTRAINT fk_produto_categoria
FOREIGN KEY (categoria_id)
REFERENCES categorias(id);

ALTER TABLE pedidos
ADD CONSTRAINT fk_pedido_cliente
FOREIGN KEY (cliente_id)
REFERENCES clientes(id);

ALTER TABLE itens_pedido
ADD CONSTRAINT fk_item_pedido
FOREIGN KEY (pedido_id)
REFERENCES pedidos(id);

ALTER TABLE itens_pedido
ADD CONSTRAINT fk_item_produto
FOREIGN KEY (produto_id)
REFERENCES produtos(id);

ALTER TABLE produtos
ADD CONSTRAINT chk_produto_preco
CHECK (preco >= 0);

ALTER TABLE produtos
ADD CONSTRAINT chk_produto_estoque
CHECK (estoque >= 0);

ALTER TABLE itens_pedido
ADD CONSTRAINT chk_item_quantidade
CHECK (quantidade > 0);

ALTER TABLE itens_pedido
ADD CONSTRAINT chk_item_preco
CHECK (preco_unitario >= 0);