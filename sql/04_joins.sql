-- Produtos com suas categorias
SELECT
    produtos.nome AS produto,
    produtos.preco,
    categorias.nome AS categoria
FROM produtos
JOIN categorias
    ON produtos.categoria_id = categorias.id;

SELECT
    pedidos.id AS pedido,
    clientes.nome AS cliente,
    pedidos.data_pedido,
    pedidos.status
FROM pedidos
JOIN clientes
    ON pedidos.cliente_id = clientes.id;

SELECT
    clientes.nome AS cliente,
    produtos.nome AS produto,
    itens_pedido.quantidade,
    itens_pedido.preco_unitario
FROM itens_pedido
JOIN pedidos
    ON itens_pedido.pedido_id = pedidos.id
JOIN clientes
    ON pedidos.cliente_id = clientes.id
JOIN produtos
    ON itens_pedido.produto_id = produtos.id;

SELECT
    pedidos.id AS pedido,
    clientes.nome AS cliente,
    produtos.nome AS produto,
    itens_pedido.quantidade,
    itens_pedido.preco_unitario,
    itens_pedido.quantidade * itens_pedido.preco_unitario AS subtotal
FROM itens_pedido
JOIN pedidos
    ON itens_pedido.pedido_id = pedidos.id
JOIN clientes
    ON pedidos.cliente_id = clientes.id
JOIN produtos
    ON itens_pedido.produto_id = produtos.id
ORDER BY pedidos.id;

SELECT
    clientes.nome AS cliente,
    pedidos.id AS pedido,
    pedidos.status
FROM clientes
LEFT JOIN pedidos
    ON clientes.id = pedidos.cliente_id
ORDER BY clientes.nome;