\set ON_ERROR_STOP on
BEGIN;
SET LOCAL plpgsql.check_asserts = on;

-- Os dados e objetos devem existir após a instalação completa.
DO $$
BEGIN
    ASSERT (SELECT count(*) = 7 FROM produtos), 'Carga de produtos incompleta';
    ASSERT (SELECT count(*) = 5 FROM clientes), 'Carga de clientes incompleta';
    ASSERT (SELECT count(*) = 4 FROM pedidos), 'Carga de pedidos incompleta';
    ASSERT (SELECT total_clientes = 5 AND total_produtos = 7 FROM dashboard_loja),
        'Dashboard inconsistente';
    ASSERT calcular_total_pedido(1) = 399.70, 'Total do pedido incorreto';
    ASSERT (SELECT count(*) = 5 FROM pedidos_detalhados), 'View de pedidos incompleta';
END;
$$;

-- Executa uma operação que precisa falhar com a mensagem esperada.
CREATE FUNCTION pg_temp.esperar_erro(comando TEXT, mensagem TEXT)
RETURNS VOID LANGUAGE plpgsql AS $$
BEGIN
    BEGIN
        EXECUTE comando;
    EXCEPTION WHEN raise_exception THEN
        IF SQLERRM = mensagem THEN
            RETURN;
        END IF;
        RAISE;
    END;
    RAISE EXCEPTION 'Operação deveria falhar: %', comando;
END;
$$;

DO $teste$
DECLARE
    estoque_inicial INTEGER;
    novo_pedido INTEGER;
    pedidos_antes INTEGER;
    movimentos_antes INTEGER;
BEGIN
    SELECT estoque INTO estoque_inicial FROM produtos WHERE id = 2;
    SELECT count(*) INTO pedidos_antes FROM pedidos;
    SELECT count(*) INTO movimentos_antes FROM movimentacoes_estoque;

    CALL registrar_venda(1, 2, 3);
    SELECT max(id) INTO novo_pedido FROM pedidos;
    ASSERT (SELECT status = 'concluido' FROM pedidos WHERE id = novo_pedido);
    ASSERT (SELECT estoque = estoque_inicial - 3 FROM produtos WHERE id = 2),
        'Venda não reduziu estoque';
    ASSERT calcular_total_pedido(novo_pedido) = 299.70, 'Venda com total incorreto';
    ASSERT (SELECT count(*) = 1 FROM itens_pedido WHERE pedido_id = novo_pedido);
    ASSERT (SELECT count(*) = movimentos_antes + 1 FROM movimentacoes_estoque);
    ASSERT (SELECT count(*) = 1 FROM movimentacoes_estoque
            WHERE produto_id = 2 AND tipo = 'saida' AND quantidade = 3);

    CALL cancelar_pedido(novo_pedido);
    ASSERT (SELECT estoque = estoque_inicial FROM produtos WHERE id = 2),
        'Cancelamento não devolveu estoque';
    ASSERT (SELECT status = 'cancelado' FROM pedidos WHERE id = novo_pedido);
    ASSERT (SELECT count(*) = 1 FROM historico_status_pedido
            WHERE pedido_id = novo_pedido
              AND status_anterior = 'concluido' AND status_novo = 'cancelado');
    ASSERT (SELECT count(*) = movimentos_antes + 2 FROM movimentacoes_estoque);
    ASSERT (SELECT count(*) = 1 FROM movimentacoes_estoque
            WHERE produto_id = 2 AND tipo = 'entrada' AND quantidade = 3);

    PERFORM pg_temp.esperar_erro(format('CALL cancelar_pedido(%s)', novo_pedido),
                               'Pedido já está cancelado');
    PERFORM pg_temp.esperar_erro('CALL cancelar_pedido(3)',
                               'Somente pedidos concluídos podem ser cancelados');
    PERFORM pg_temp.esperar_erro('CALL cancelar_pedido(-1)', 'Pedido não encontrado');
    PERFORM pg_temp.esperar_erro('CALL registrar_venda(1, 2, 1000000)', 'Estoque insuficiente');
    PERFORM pg_temp.esperar_erro('CALL registrar_venda(1, -1, 1)', 'Produto não encontrado');
    PERFORM pg_temp.esperar_erro('CALL registrar_venda(-1, 2, 1)', 'Cliente não encontrado');
    PERFORM pg_temp.esperar_erro('CALL registrar_venda(1, 2, 0)', 'Quantidade deve ser maior que zero');
    PERFORM pg_temp.esperar_erro('CALL registrar_venda(1, 2, -1)', 'Quantidade deve ser maior que zero');
    PERFORM pg_temp.esperar_erro('CALL registrar_venda(1, 2, NULL)', 'Quantidade deve ser maior que zero');
    PERFORM pg_temp.esperar_erro(
        $$INSERT INTO movimentacoes_estoque (produto_id, tipo, quantidade)
          VALUES (2, 'saida', 1000000)$$,
        'Estoque insuficiente para o produto 2');

    ASSERT (SELECT estoque = estoque_inicial FROM produtos WHERE id = 2),
        'Operação rejeitada alterou estoque';
    ASSERT (SELECT count(*) = pedidos_antes + 1 FROM pedidos),
        'Operação rejeitada deixou pedido parcial';
    ASSERT (SELECT count(*) = movimentos_antes + 2 FROM movimentacoes_estoque),
        'Operação rejeitada deixou movimentação parcial';
    ASSERT (SELECT count(*) = 1 FROM historico_status_pedido WHERE pedido_id = novo_pedido),
        'Cancelamento repetido alterou histórico';

    ASSERT NOT produto_disponivel(-1, 1);
    ASSERT NOT produto_disponivel(2, 0);
    ASSERT NOT produto_disponivel(2, -1);
    ASSERT NOT produto_disponivel(2, NULL);
    ASSERT produto_disponivel(2, estoque_inicial);

    UPDATE pedidos SET status = 'em_preparacao' WHERE id = 3;
    ASSERT (SELECT status_novo = 'em_preparacao' FROM historico_status_pedido WHERE pedido_id = 3);
END;
$teste$;

-- Rollback preserva os dados, mas sequências de IDs podem avançar.
ROLLBACK;
\echo 'Regressão concluída: instalação, venda, cancelamento e validações passaram.'
