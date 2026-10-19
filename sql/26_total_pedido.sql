CREATE OR REPLACE FUNCTION calcular_total_pedido(p_pedido_id INTEGER)
RETURNS DECIMAL(10,2)
LANGUAGE SQL
AS $$
    SELECT COALESCE((
        SELECT COALESCE(SUM(ip.quantidade * ip.preco_unitario), 0) - pe.desconto + pe.frete
        FROM pedidos pe
        LEFT JOIN itens_pedido ip ON ip.pedido_id = pe.id
        WHERE pe.id = p_pedido_id
        GROUP BY pe.id
    ), 0);
$$;
