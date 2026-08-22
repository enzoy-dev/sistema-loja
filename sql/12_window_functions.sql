SELECT
    produtos.nome AS produto,
    SUM(itens_pedido.quantidade) AS quantidade_vendida,

    RANK() OVER (
        ORDER BY SUM(itens_pedido.quantidade) DESC
    ) AS ranking

FROM produtos

JOIN itens_pedido
    ON produtos.id = itens_pedido.produto_id

GROUP BY produtos.id, produtos.nome;

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
    total_gasto,

    RANK() OVER (
        ORDER BY total_gasto DESC
    ) AS ranking

FROM gastos_clientes
ORDER BY ranking;


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
    total_gasto,

    ROW_NUMBER() OVER (
        ORDER BY total_gasto DESC
    ) AS numero

FROM gastos_clientes


SELECT
    pedidos.id AS pedido,
    pedidos.data_pedido,

    SUM(
        itens_pedido.quantidade *
        itens_pedido.preco_unitario
    ) AS total_pedido,

    SUM(
        SUM(
            itens_pedido.quantidade *
            itens_pedido.preco_unitario
        )
    ) OVER (
        ORDER BY pedidos.id
    ) AS total_acumulado

FROM pedidos

JOIN itens_pedido
    ON pedidos.id = itens_pedido.pedido_id

GROUP BY pedidos.id, pedidos.data_pedido

ORDER BY pedidos.id;