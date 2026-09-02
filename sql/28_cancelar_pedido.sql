CREATE OR REPLACE PROCEDURE cancelar_pedido(
    p_pedido_id INTEGER
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_status VARCHAR(30);
BEGIN

    SELECT status
    INTO v_status
    FROM pedidos
    WHERE id = p_pedido_id
    FOR UPDATE;

    IF v_status IS NULL THEN
        RAISE EXCEPTION 'Pedido não encontrado';
    END IF;

    IF v_status = 'cancelado' THEN
        RAISE EXCEPTION 'Pedido já está cancelado';
    END IF;

    IF v_status <> 'concluido' THEN
        RAISE EXCEPTION
            'Somente pedidos concluídos podem ser cancelados';
    END IF;

    UPDATE pedidos
    SET status = 'cancelado'
    WHERE id = p_pedido_id;

    INSERT INTO movimentacoes_estoque (
        produto_id,
        tipo,
        quantidade
    )
    SELECT
        produto_id,
        'entrada',
        quantidade
    FROM itens_pedido
    WHERE pedido_id = p_pedido_id;

END;
$$;