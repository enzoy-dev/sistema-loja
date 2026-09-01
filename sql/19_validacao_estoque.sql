CREATE OR REPLACE FUNCTION atualizar_estoque()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    estoque_atual INTEGER;
BEGIN

    SELECT estoque
    INTO estoque_atual
    FROM produtos
    WHERE id = NEW.produto_id;

    IF NEW.tipo = 'saida' THEN

        IF estoque_atual < NEW.quantidade THEN
            RAISE EXCEPTION
                'Estoque insuficiente para o produto %',
                NEW.produto_id;
        END IF;

        UPDATE produtos
        SET estoque = estoque - NEW.quantidade
        WHERE id = NEW.produto_id;

    ELSIF NEW.tipo = 'entrada' THEN

        UPDATE produtos
        SET estoque = estoque + NEW.quantidade
        WHERE id = NEW.produto_id;

    END IF;

    RETURN NEW;

END;
$$;