CREATE OR REPLACE VIEW dashboard_loja AS

SELECT

    (
        SELECT COUNT(*)
        FROM clientes
    ) AS total_clientes,

    (
        SELECT COUNT(*)
        FROM produtos
    ) AS total_produtos,

    (
        SELECT COUNT(*)
        FROM pedidos
        WHERE status = 'concluido'
    ) AS pedidos_concluidos,

    (
        SELECT COALESCE(
            SUM(
                quantidade * preco_unitario
            ),
            0
        )
        FROM itens_pedido
        JOIN pedidos
            ON itens_pedido.pedido_id = pedidos.id
        WHERE pedidos.status = 'concluido'
    ) AS faturamento,

    (
        SELECT COALESCE(
            SUM(estoque),
            0
        )
        FROM produtos
    ) AS estoque_total;