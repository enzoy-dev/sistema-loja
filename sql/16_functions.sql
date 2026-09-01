CREATE OR REPLACE FUNCTION calcular_total_pedido(p_pedido_id INTEGER)
RETURNS DECIMAL(10,2)
LANGUAGE SQL
AS $$
    SELECT COALESCE(
        SUM(quantidade * preco_unitario),
        0
    )
    FROM itens_pedido
    WHERE pedido_id = p_pedido_id;
$$;