INSERT INTO clientes (nome, email, telefone, data_cadastro)
VALUES
    ('Carlos Silva', 'carlos@email.com', '11999990001', '2026-08-19'),
    ('Ana Souza', 'ana@email.com', '11999990002', '2026-08-19'),
    ('Lucas Oliveira', 'lucas@email.com', '11999990003', '2026-08-20'),
    ('Mariana Santos', 'mariana@email.com', '11999990004', '2026-08-20'),
    ('Pedro Costa', 'pedro@email.com', '11999990005', '2026-08-21');

INSERT INTO produtos (id, nome, preco, estoque, categoria_id)
VALUES
    (1, 'Notebook', 3500.00, 10, 1),
    (2, 'Mouse', 99.90, 50, 1),
    (3, 'Teclado', 199.90, 30, 1),
    (4, 'Camiseta', 79.90, 40, 2),
    (5, 'Calca Jeans', 149.90, 20, 2),
    (6, 'Chocolate', 8.50, 100, 3),
    (7, 'Resident Evil 4', 249.90, 15, 4);

INSERT INTO pedidos (id, cliente_id, data_pedido, status)
VALUES
    (1, 1, '2026-08-20', 'concluido'),
    (2, 2, '2026-08-20', 'concluido'),
    (3, 1, '2026-08-21', 'pendente'),
    (4, 4, '2026-08-21', 'concluido');

INSERT INTO itens_pedido
    (id, pedido_id, produto_id, quantidade, preco_unitario)
VALUES
    (1, 1, 2, 2, 99.90),
    (2, 1, 3, 1, 199.90),
    (3, 2, 7, 1, 249.90),
    (4, 3, 1, 1, 3500.00),
    (5, 4, 4, 2, 79.90);