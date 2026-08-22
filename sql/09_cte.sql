WITH gastos_clientes AS (
    SELECT
        clientes.id,
        clientes.nome,
        SUM(
            itens_pedido.quantidade *
            itens_pedido.preco_unitario
        ) AS total_gasto
    FROM clientes
    JOIN pedidos
        ON clientes.id = pedidos.cliente_id
    JOIN itens_pedido
        ON pedidos.id = itens_pedido.pedido_id
    GROUP BY clientes.id, clientes.nome
)

SELECT *
FROM gastos_clientes
ORDER BY total_gasto DESC;

WITH gastos_clientes AS (
    SELECT
        clientes.id,
        clientes.nome,
        SUM(
            itens_pedido.quantidade *
            itens_pedido.preco_unitario
        ) AS total_gasto
    FROM clientes
    JOIN pedidos
        ON clientes.id = pedidos.cliente_id
    JOIN itens_pedido
        ON pedidos.id = itens_pedido.pedido_id
    GROUP BY clientes.id, clientes.nome
)

SELECT
    nome,
    total_gasto
FROM gastos_clientes
WHERE total_gasto > (
    SELECT AVG(total_gasto)
    FROM gastos_clientes
)
ORDER BY total_gasto DESC;