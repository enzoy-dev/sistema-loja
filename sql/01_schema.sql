CREATE TABLE categorias (
    id INTEGER PRIMARY KEY,
    nome VARCHAR(100) NOT NULL
);

CREATE TABLE clientes (
    id INTEGER PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL,
    telefone VARCHAR(20),
    data_cadastro DATE NOT NULL
);

CREATE TABLE produtos (
    id INTEGER PRIMARY KEY,
    nome VARCHAR(150) NOT NULL,
    preco DECIMAL(10, 2) NOT NULL,
    estoque INTEGER NOT NULL,
    categoria_id INTEGER NOT NULL
);

CREATE TABLE pedidos (
    id INTEGER PRIMARY KEY,
    cliente_id INTEGER NOT NULL,
    data_pedido DATE NOT NULL,
    status VARCHAR(30) NOT NULL
);

CREATE TABLE itens_pedido (
    id INTEGER PRIMARY KEY,
    pedido_id INTEGER NOT NULL,
    produto_id INTEGER NOT NULL,
    quantidade INTEGER NOT NULL,
    preco_unitario DECIMAL(10, 2) NOT NULL
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