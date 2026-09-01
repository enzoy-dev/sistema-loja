CREATE OR REPLACE FUNCTION verificar_estoque(
    p_produto_id INTEGER
)
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    quantidade_estoque INTEGER;
BEGIN

    SELECT estoque
    INTO quantidade_estoque
    FROM produtos
    WHERE id = p_produto_id;

    RETURN COALESCE(quantidade_estoque, 0);

END;
$$;

CREATE OR REPLACE FUNCTION produto_disponivel(
    p_produto_id INTEGER,
    p_quantidade INTEGER
)
RETURNS BOOLEAN
LANGUAGE plpgsql
AS $$
DECLARE
    estoque_atual INTEGER;
BEGIN

    SELECT estoque
    INTO estoque_atual
    FROM produtos
    WHERE id = p_produto_id;

    RETURN COALESCE(estoque_atual, 0) >= p_quantidade;

END;
$$;