from decimal import Decimal

import psycopg
from psycopg.types.json import Jsonb
import pytest


@pytest.mark.parametrize('itens,desconto,frete', [
    ([], '0', '0'),
    (None, '0', '0'),
    ({'produto_id': 2, 'quantidade': 1}, '0', '0'),
    ([None], '0', '0'),
    ([{'produto_id': 2}], '0', '0'),
    ([{'produto_id': 2, 'quantidade': 0}], '0', '0'),
    ([{'produto_id': 2, 'quantidade': None}], '0', '0'),
    ([{'produto_id': 2, 'quantidade': '1'}], '0', '0'),
    ([{'produto_id': True, 'quantidade': 1}], '0', '0'),
    ([{'produto_id': 2, 'quantidade': 1.5}], '0', '0'),
    ([{'produto_id': 2, 'quantidade': 2147483648}], '0', '0'),
    ([{'produto_id': 2, 'quantidade': 1}, {'produto_id': 2, 'quantidade': 2}], '0', '0'),
    ([{'produto_id': 2, 'quantidade': 1}], '-1', '0'),
    ([{'produto_id': 2, 'quantidade': 1}], '0', '-1'),
    ([{'produto_id': 2, 'quantidade': 1}], '0.001', '0'),
    ([{'produto_id': 2, 'quantidade': 1}], '100', '0'),
    ([{'produto_id': 2, 'quantidade': 1}], 'NaN', '0'),
    ([{'produto_id': 2, 'quantidade': 1}], '0', 'Infinity'),
    ([{'produto_id': 2, 'quantidade': 1}], None, '0'),
    ([{'produto_id': 2, 'quantidade': 1}], '0', '99999999.99'),
    ([{'produto_id': 2, 'quantidade': 1}, {'produto_id': 3, 'quantidade': 31}], '0', '0'),
])
def test_sql_rejects_invalid_checkout(connection, itens, desconto, frete):
    before = connection.execute('SELECT array_agg(estoque ORDER BY id) AS stocks FROM produtos').fetchone()
    with pytest.raises(psycopg.errors.RaiseException):
        connection.execute('SELECT registrar_pedido(1, %s, %s::numeric, %s::numeric)',
                           (Jsonb(itens), desconto, frete))
    assert connection.execute('SELECT count(*) AS n FROM pedidos').fetchone()['n'] == 4
    assert connection.execute('SELECT count(*) AS n FROM itens_pedido').fetchone()['n'] == 5
    assert connection.execute('SELECT count(*) AS n FROM movimentacoes_estoque').fetchone()['n'] == 0
    assert connection.execute('SELECT array_agg(estoque ORDER BY id) AS stocks FROM produtos').fetchone() == before


def test_sql_defaults_and_legacy_sale(connection):
    row = connection.execute('''SELECT registrar_pedido(1,
        '[{"produto_id":2,"quantidade":2},{"produto_id":3,"quantidade":1}]') AS id''').fetchone()
    assert connection.execute('SELECT calcular_total_pedido(%s) AS total', (row['id'],)).fetchone()['total'] == Decimal('399.70')
    connection.execute('CALL registrar_venda(1, 2, 1)')
    assert connection.execute('SELECT estoque FROM produtos WHERE id=2').fetchone()['estoque'] == 47


def test_prices_and_stock_roll_back_if_late_movement_fails(connection):
    # Simula falha depois de inserir pedido, itens e a primeira movimentação.
    connection.execute('''CREATE FUNCTION rejeitar_segundo_item() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN IF NEW.produto_id = 3 THEN RAISE EXCEPTION 'Falha simulada'; END IF; RETURN NEW; END;
        $$''')
    connection.execute('''CREATE TRIGGER teste_falha BEFORE INSERT ON movimentacoes_estoque
        FOR EACH ROW EXECUTE FUNCTION rejeitar_segundo_item()''')
    with pytest.raises(psycopg.errors.RaiseException, match='Falha simulada'):
        connection.execute('''SELECT registrar_pedido(1,
            '[{"produto_id":2,"quantidade":2},{"produto_id":3,"quantidade":1}]', 20, 15)''')
    assert connection.execute('SELECT estoque FROM produtos WHERE id=2').fetchone()['estoque'] == 50
    assert connection.execute('SELECT count(*) AS n FROM pedidos').fetchone()['n'] == 4
    assert connection.execute('SELECT count(*) AS n FROM itens_pedido').fetchone()['n'] == 5
    assert connection.execute('SELECT count(*) AS n FROM movimentacoes_estoque').fetchone()['n'] == 0
