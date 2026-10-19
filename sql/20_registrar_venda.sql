-- Compatibilidade com o fluxo original de venda de um produto.
CREATE OR REPLACE PROCEDURE registrar_venda(
    p_cliente_id INTEGER,
    p_produto_id INTEGER,
    p_quantidade INTEGER
)
LANGUAGE plpgsql
AS $$
BEGIN
    IF p_quantidade IS NULL OR p_quantidade <= 0 THEN
        RAISE EXCEPTION 'Quantidade deve ser maior que zero';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM clientes WHERE id = p_cliente_id) THEN
        RAISE EXCEPTION 'Cliente não encontrado';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM produtos WHERE id = p_produto_id) THEN
        RAISE EXCEPTION 'Produto não encontrado';
    END IF;
    PERFORM registrar_pedido(p_cliente_id, jsonb_build_array(
        jsonb_build_object('produto_id', p_produto_id, 'quantidade', p_quantidade)
    ));
END;
$$;
