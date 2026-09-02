CREATE OR REPLACE FUNCTION produtos_estoque_baixo(
    p_limite INTEGER
)
RETURNS TABLE (
    produto_id INTEGER,
    produto_nome VARCHAR,
    estoque_atual INTEGER
)
LANGUAGE plpgsql
AS $$
BEGIN

    RETURN QUERY
    SELECT
        p.id,
        p.nome,
        p.estoque
    FROM produtos p
    WHERE p.estoque <= p_limite
    ORDER BY p.estoque ASC;

END;
$$;