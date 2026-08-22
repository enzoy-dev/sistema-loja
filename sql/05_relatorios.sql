SELECT
    pedido_id,
    SUM(quantidade * preco_unitario) AS total
FROM itens_pedido
GROUP BY pedido_id;

SELECT
    clientes.nome AS cliente,
    SUM(
        itens_pedido.quantidade * itens_pedido.preco_unitario
    ) AS total_gasto
FROM clientes
JOIN pedidos
    ON clientes.id = pedidos.cliente_id
JOIN itens_pedido
    ON pedidos.id = itens_pedido.pedido_id
GROUP BY clientes.id, clientes.nome
ORDER BY total_gasto DESC;

SELECT
    clientes.nome AS cliente,
    SUM(
        itens_pedido.quantidade * itens_pedido.preco_unitario
    ) AS total_gasto
FROM clientes
JOIN pedidos
    ON clientes.id = pedidos.cliente_id
JOIN itens_pedido
    ON pedidos.id = itens_pedido.pedido_id
GROUP BY clientes.id, clientes.nome
HAVING SUM(
    itens_pedido.quantidade * itens_pedido.preco_unitario
) > 300
ORDER BY total_gasto DESC;

SELECT
    produtos.nome AS produto,
    SUM(itens_pedido.quantidade) AS quantidade_vendida
FROM produtos
JOIN itens_pedido
    ON produtos.id = itens_pedido.produto_id
GROUP BY produtos.id, produtos.nome
ORDER BY quantidade_vendida DESC
LIMIT 1;