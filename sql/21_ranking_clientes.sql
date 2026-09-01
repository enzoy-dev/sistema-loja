WITH gastos AS (

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

    WHERE pedidos.status = 'concluido'

    GROUP BY
        clientes.id,
        clientes.nome
)

SELECT
    nome,
    total_gasto,

    RANK() OVER (
        ORDER BY total_gasto DESC
    ) AS ranking

FROM gastos

ORDER BY ranking;