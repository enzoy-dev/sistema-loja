CREATE OR REPLACE FUNCTION calcular_total_pedido(
    p_pedido_id INTEGER
)
RETURNS DECIMAL(10,2)
LANGUAGE plpgsql
AS $$
DECLARE
    total DECIMAL(10,2);
BEGIN

    SELECT COALESCE(
        SUM(quantidade * preco_unitario),
        0
    )
    INTO total
    FROM itens_pedido
    WHERE pedido_id = p_pedido_id;

    RETURN total;

END;
$$;