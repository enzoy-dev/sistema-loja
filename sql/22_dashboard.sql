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
        SELECT COALESCE(SUM(t.subtotal - pe.desconto + pe.frete), 0)
        FROM pedidos pe
        JOIN (
            SELECT pedido_id, SUM(quantidade * preco_unitario) AS subtotal
            FROM itens_pedido GROUP BY pedido_id
        ) t ON t.pedido_id = pe.id
        WHERE pe.status = 'concluido'
    ) AS faturamento,

    (
        SELECT COALESCE(
            SUM(estoque),
            0
        )
        FROM produtos
    ) AS estoque_total;