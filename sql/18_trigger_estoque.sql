CREATE OR REPLACE FUNCTION atualizar_estoque()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN

    IF NEW.tipo = 'entrada' THEN

        UPDATE produtos
        SET estoque = estoque + NEW.quantidade
        WHERE id = NEW.produto_id;

    ELSIF NEW.tipo = 'saida' THEN

        UPDATE produtos
        SET estoque = estoque - NEW.quantidade
        WHERE id = NEW.produto_id;

    END IF;

    RETURN NEW;

END;
$$;

CREATE TRIGGER trigger_atualizar_estoque
AFTER INSERT ON movimentacoes_estoque
FOR EACH ROW
EXECUTE FUNCTION atualizar_estoque();