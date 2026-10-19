from decimal import Decimal

import pytest


def order(**overrides):
    return {'cliente_id': 1, 'itens': [{'produto_id': 2, 'quantidade': 2},
                                    {'produto_id': 3, 'quantidade': 1}],
            'desconto': '20.00', 'frete': '15.00', **overrides}


def snapshot(connection):
    return connection.execute('''SELECT
        (SELECT count(*) FROM pedidos) AS pedidos,
        (SELECT count(*) FROM itens_pedido) AS itens,
        (SELECT count(*) FROM movimentacoes_estoque) AS movimentos,
        (SELECT sum(estoque) FROM produtos) AS estoque''').fetchone()


def test_checkout_and_cancellation(client, connection):
    before = snapshot(connection)
    revenue_before = connection.execute('SELECT faturamento FROM dashboard_loja').fetchone()['faturamento']
    response = client.post('/pedidos', json=order())
    assert response.status_code == 201, response.text
    data = response.json()
    assert data['status'] == 'concluido'
    assert len(data['itens']) == 2
    assert Decimal(data['subtotal']) == Decimal('399.70')
    assert Decimal(data['total']) == Decimal('394.70')
    assert client.get('/produtos/2').json()['estoque'] == 48
    assert client.get('/produtos/3').json()['estoque'] == 29
    assert connection.execute('SELECT faturamento FROM dashboard_loja').fetchone()['faturamento'] == revenue_before + Decimal('394.70')
    assert client.get(f"/pedidos/{data['id']}").json() == data
    assert any(p['id'] == data['id'] for p in client.get('/pedidos').json())
    details = connection.execute('SELECT total_pedido FROM pedidos_detalhados WHERE pedido_id=%s', (data['id'],)).fetchall()
    assert len(details) == 2 and all(r['total_pedido'] == Decimal('394.70') for r in details)
    cancelled = client.post(f"/pedidos/{data['id']}/cancelar")
    assert cancelled.status_code == 200 and cancelled.json()['status'] == 'cancelado'
    assert client.get('/produtos/2').json()['estoque'] == 50
    assert client.get('/produtos/3').json()['estoque'] == 30
    assert connection.execute('SELECT faturamento FROM dashboard_loja').fetchone()['faturamento'] == revenue_before
    assert connection.execute('SELECT count(*) AS n FROM historico_status_pedido WHERE pedido_id=%s', (data['id'],)).fetchone()['n'] == 1
    after = snapshot(connection)
    assert after['pedidos'] == before['pedidos'] + 1
    assert after['itens'] == before['itens'] + 2
    assert after['movimentos'] == before['movimentos'] + 4
    assert after['estoque'] == before['estoque']
    assert client.post(f"/pedidos/{data['id']}/cancelar").status_code == 409
    assert snapshot(connection) == after


@pytest.mark.parametrize('overrides,code', [
    ({'cliente_id': 999999}, 404),
    ({'itens': [{'produto_id': 2, 'quantidade': 1}, {'produto_id': 999999, 'quantidade': 1}]}, 404),
    ({'itens': [{'produto_id': 2, 'quantidade': 1}, {'produto_id': 3, 'quantidade': 999999}]}, 409),
    ({'desconto': '400.00'}, 409),
    ({'desconto': '-0.01'}, 422),
    ({'frete': '-1'}, 422),
    ({'frete': '1.001'}, 422),
    ({'desconto': 'NaN'}, 422),
    ({'frete': 'Infinity'}, 422),
    ({'desconto': None}, 422),
    ({'itens': []}, 422),
    ({'itens': [{'produto_id': 2, 'quantidade': 0}]}, 422),
    ({'itens': [{'produto_id': 2, 'quantidade': -1}]}, 422),
    ({'itens': [{'produto_id': 2, 'quantidade': True}]}, 422),
    ({'itens': [{'produto_id': 2, 'quantidade': 1.5}]}, 422),
    ({'itens': [{'produto_id': 2, 'quantidade': 1}, {'produto_id': 2, 'quantidade': 2}]}, 422),
    ({'itens': [{'produto_id': 2, 'quantidade': 1, 'preco_unitario': '0.01'}]}, 422),
    ({'total': '0.01'}, 422),
])
def test_invalid_orders_are_atomic(client, connection, overrides, code):
    before = snapshot(connection)
    response = client.post('/pedidos', json=order(**overrides))
    assert response.status_code == code, response.text
    assert snapshot(connection) == before


def test_free_order_and_shipping(client):
    response = client.post('/pedidos', json=order(desconto='399.70', frete='0'))
    assert response.status_code == 201
    assert Decimal(response.json()['total']) == 0


def test_prices_are_snapshotted(client, connection):
    data = client.post('/pedidos', json=order()).json()
    connection.execute('UPDATE produtos SET preco = 1 WHERE id = 2')
    stored = client.get(f"/pedidos/{data['id']}").json()
    assert Decimal(stored['total']) == Decimal('394.70')
    assert Decimal(stored['itens'][0]['preco_unitario']) == Decimal('99.90')


def test_catalog_and_stock_entry(client, connection):
    assert client.get('/health').json() == {'status': 'ok'}
    category = client.post('/categorias', json={'nome': 'Livros'})
    assert category.status_code == 201
    customer = client.post('/clientes', json={'nome': 'Cliente Teste', 'email': 'cliente@example.com'})
    assert customer.status_code == 201
    assert any(c['id'] == customer.json()['id'] for c in client.get('/clientes').json())
    assert any(c['id'] == category.json()['id'] for c in client.get('/categorias').json())
    product = client.post('/produtos', json={'nome': 'Livro SQL', 'preco': '49.90', 'categoria_id': category.json()['id']})
    assert product.status_code == 201, product.text
    product_id = product.json()['id']
    assert product.json()['estoque'] == 0
    assert client.post(f'/produtos/{product_id}/entradas', json={'quantidade': 5}).json()['estoque'] == 5
    assert connection.execute('SELECT quantidade FROM movimentacoes_estoque WHERE produto_id=%s', (product_id,)).fetchone()['quantidade'] == 5
    assert len(client.get('/produtos?limit=2&offset=1').json()) == 2
    assert client.get('/produtos?limit=101').status_code == 422
    assert client.get('/produtos?offset=-1').status_code == 422
    assert client.post('/clientes', json={'nome': 'Outro Cliente', 'email': 'cliente@example.com'}).status_code == 409
    assert client.post('/clientes', json={'nome': 'Outro Cliente', 'email': 'invalido'}).status_code == 422
    assert client.post('/categorias', json={'nome': '  '}).status_code == 422
    assert client.post('/produtos', json={'nome': 'Produto', 'preco': '1.00', 'categoria_id': 999999}).status_code == 422
    assert client.post(f'/produtos/{product_id}/entradas', json={'quantidade': 0}).status_code == 422
    assert client.post(f'/produtos/{product_id}/entradas', json={'quantidade': 2147483647}).status_code == 422
    assert client.get(f'/produtos/{product_id}').json()['estoque'] == 5


@pytest.mark.parametrize('method,path', [
    ('get', '/produtos/999999'), ('get', '/pedidos/999999'),
    ('post', '/pedidos/999999/cancelar'),
])
def test_missing_resources(client, method, path):
    assert getattr(client, method)(path).status_code == 404


def test_cannot_cancel_pending_order(client, connection):
    before = snapshot(connection)
    assert client.post('/pedidos/3/cancelar').status_code == 409
    assert snapshot(connection) == before
