-- Todos os itens e movimentos são confirmados ou desfeitos juntos.
CREATE OR REPLACE FUNCTION registrar_pedido(
    p_cliente_id INTEGER,
    p_itens JSONB,
    p_desconto NUMERIC DEFAULT 0,
    p_frete NUMERIC DEFAULT 0
)
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    item JSONB;
    produto RECORD;
    novo_pedido INTEGER;
    subtotal NUMERIC := 0;
    produtos_encontrados INTEGER := 0;
BEGIN
    IF NOT EXISTS (SELECT 1 FROM clientes WHERE id = p_cliente_id) THEN
        RAISE EXCEPTION 'Cliente não encontrado';
    END IF;
    IF p_itens IS NULL OR jsonb_typeof(p_itens) <> 'array' THEN
        RAISE EXCEPTION 'Itens devem ser uma lista não vazia';
    END IF;
    IF jsonb_array_length(p_itens) = 0 THEN
        RAISE EXCEPTION 'Itens devem ser uma lista não vazia';
    END IF;
    FOR item IN SELECT value FROM jsonb_array_elements(p_itens) LOOP
        IF jsonb_typeof(item) <> 'object'
           OR jsonb_typeof(item -> 'produto_id') IS DISTINCT FROM 'number'
           OR jsonb_typeof(item -> 'quantidade') IS DISTINCT FROM 'number'
           OR (item ->> 'produto_id') !~ '^[1-9][0-9]*$'
           OR (item ->> 'quantidade') !~ '^[1-9][0-9]*$' THEN
            RAISE EXCEPTION 'Cada item deve ter produto_id e quantidade inteiros positivos';
        END IF;
        IF (item ->> 'produto_id')::numeric > 2147483647
           OR (item ->> 'quantidade')::numeric > 2147483647 THEN
            RAISE EXCEPTION 'Produto ou quantidade fora do limite permitido';
        END IF;
    END LOOP;
    IF EXISTS (
        SELECT 1 FROM jsonb_to_recordset(p_itens) AS i(produto_id INTEGER, quantidade INTEGER)
        GROUP BY produto_id HAVING count(*) > 1
    ) THEN
        RAISE EXCEPTION 'Produto repetido no pedido';
    END IF;
    IF p_desconto IS NULL OR p_frete IS NULL
       OR p_desconto < 0 OR p_frete < 0
       OR p_desconto > 99999999.99 OR p_frete > 99999999.99
       OR p_desconto <> round(p_desconto, 2) OR p_frete <> round(p_frete, 2) THEN
        RAISE EXCEPTION 'Desconto e frete devem ser valores não negativos com até duas casas decimais';
    END IF;

    -- A ordem estável de bloqueio evita deadlocks entre pedidos com os mesmos produtos.
    FOR produto IN
        SELECT p.id, p.preco, p.estoque, i.quantidade
        FROM jsonb_to_recordset(p_itens) AS i(produto_id INTEGER, quantidade INTEGER)
        JOIN produtos p ON p.id = i.produto_id
        ORDER BY p.id
        FOR UPDATE OF p
    LOOP
        IF produto.estoque < produto.quantidade THEN
            RAISE EXCEPTION 'Estoque insuficiente';
        END IF;
        subtotal := subtotal + produto.preco * produto.quantidade;
        produtos_encontrados := produtos_encontrados + 1;
    END LOOP;
    IF produtos_encontrados <> jsonb_array_length(p_itens) THEN
        RAISE EXCEPTION 'Produto não encontrado';
    END IF;
    IF p_desconto > subtotal THEN
        RAISE EXCEPTION 'Desconto não pode ultrapassar o subtotal';
    END IF;
    IF subtotal - p_desconto + p_frete > 99999999.99 THEN
        RAISE EXCEPTION 'Total do pedido fora do limite permitido';
    END IF;

    INSERT INTO pedidos (cliente_id, data_pedido, status, desconto, frete)
    VALUES (p_cliente_id, CURRENT_DATE, 'concluido', p_desconto, p_frete)
    RETURNING id INTO novo_pedido;

    INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario)
    SELECT novo_pedido, p.id, i.quantidade, p.preco
    FROM jsonb_to_recordset(p_itens) AS i(produto_id INTEGER, quantidade INTEGER)
    JOIN produtos p ON p.id = i.produto_id;

    INSERT INTO movimentacoes_estoque (produto_id, tipo, quantidade)
    SELECT produto_id, 'saida', quantidade
    FROM itens_pedido WHERE pedido_id = novo_pedido ORDER BY produto_id;

    RETURN novo_pedido;
END;
$$;
