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

    RETURN estoque_atual IS NOT NULL
        AND p_quantidade IS NOT NULL
        AND p_quantidade > 0
        AND estoque_atual >= p_quantidade;

END;
$$;