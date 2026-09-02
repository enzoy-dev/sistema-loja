-- Categorias
INSERT INTO categorias (nome) VALUES
    ('Eletrônicos'),
    ('Roupas'),
    ('Alimentos'),
    ('Games');

-- Clientes
INSERT INTO clientes (nome, email, telefone, data_cadastro) VALUES
    ('Carlos Silva', 'carlos@email.com', '11999990001', '2026-08-19'),
    ('Ana Souza', 'ana@email.com', '11999990002', '2026-08-19'),
    ('Lucas Oliveira', 'lucas@email.com', '11999990003', '2026-08-20'),
    ('Mariana Santos', 'mariana@email.com', '11999990004', '2026-08-20'),
    ('Pedro Costa', 'pedro@email.com', '11999990005', '2026-08-21');

-- Produtos
INSERT INTO produtos (nome, preco, estoque, categoria_id) VALUES
    ('Notebook', 3500.00, 10, 1),
    ('Mouse', 99.90, 50, 1),
    ('Teclado', 199.90, 30, 1),
    ('Camiseta', 79.90, 40, 2),
    ('Calça Jeans', 149.90, 20, 2),
    ('Chocolate', 8.50, 100, 3),


-- Pedidos
INSERT INTO pedidos (cliente_id, data_pedido, status) VALUES
    (1, '2026-08-20', 'concluido'),
    (2, '2026-08-20', 'concluido'),
    (1, '2026-08-21', 'pendente'),
    (4, '2026-08-21', 'concluido');

-- Itens do pedido
INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES
    (1, 2, 2, 99.90),
    (1, 3, 1, 199.90),
    (2, 7, 1, 249.90),
    (3, 1, 1, 3500.00),
    (4, 4, 2, 79.90);