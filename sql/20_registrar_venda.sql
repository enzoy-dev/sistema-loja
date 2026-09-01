CREATE OR REPLACE PROCEDURE registrar_venda(
    p_cliente_id INTEGER,
    p_produto_id INTEGER,
    p_quantidade INTEGER
)
LANGUAGE plpgsql
AS $$
DECLARE
    novo_pedido_id INTEGER;
    preco_produto DECIMAL(10,2);
BEGIN

    SELECT preco
    INTO preco_produto
    FROM produtos
    WHERE id = p_produto_id;

    IF preco_produto IS NULL THEN
        RAISE EXCEPTION 'Produto não encontrado';
    END IF;

    IF NOT produto_disponivel(
        p_produto_id,
        p_quantidade
    ) THEN
        RAISE EXCEPTION 'Estoque insuficiente';
    END IF;

    INSERT INTO pedidos (
        cliente_id,
        data_pedido,
        status
    )
    VALUES (
        p_cliente_id,
        CURRENT_DATE,
        'concluido'
    )
    RETURNING id INTO novo_pedido_id;

    INSERT INTO itens_pedido (
        pedido_id,
        produto_id,
        quantidade,
        preco_unitario
    )
    VALUES (
        novo_pedido_id,
        p_produto_id,
        p_quantidade,
        preco_produto
    );

    INSERT INTO movimentacoes_estoque (
        produto_id,
        tipo,
        quantidade
    )
    VALUES (
        p_produto_id,
        'saida',
        p_quantidade
    );

END;
$$;