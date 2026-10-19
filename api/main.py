from typing import Annotated

import psycopg
from fastapi import Depends, FastAPI, HTTPException, Path, Query, Request
from fastapi.responses import JSONResponse
from psycopg.types.json import Jsonb

from api.db import get_connection
from api.schemas import (
    CategoriaInput, ClienteInput, Pedido, PedidoInput, Produto, ProdutoInput, QuantidadeInput,
)

app = FastAPI(title='Sistema de Loja', version='1.0.0')
Connection = Annotated[psycopg.Connection, Depends(get_connection)]
ResourceId = Annotated[int, Path(gt=0, le=2147483647)]
Limit = Annotated[int, Query(ge=1, le=100)]
Offset = Annotated[int, Query(ge=0)]


@app.exception_handler(psycopg.Error)
def database_error(request: Request, error: psycopg.Error):
    if isinstance(error, psycopg.errors.RaiseException):
        message = error.diag.message_primary
        code = 404 if message in {'Cliente não encontrado', 'Produto não encontrado', 'Pedido não encontrado'} else 409
    elif isinstance(error, psycopg.errors.UniqueViolation):
        code, message = 409, 'Já existe um cadastro com esses dados'
    elif isinstance(error, (psycopg.errors.CheckViolation, psycopg.errors.ForeignKeyViolation,
                            psycopg.errors.NumericValueOutOfRange)):
        code, message = 422, 'Dados incompatíveis com as regras do banco'
    elif isinstance(error, (psycopg.errors.DeadlockDetected, psycopg.errors.SerializationFailure)):
        code, message = 409, 'Conflito de transação; tente novamente'
    elif isinstance(error, psycopg.OperationalError):
        code, message = 503, 'Banco de dados indisponível'
    else:
        code, message = 500, 'Erro interno no banco de dados'
    return JSONResponse(status_code=code, content={'detail': message})


def read_order(connection, pedido_id):
    order = connection.execute('''
        SELECT pe.*, COALESCE((SELECT SUM(quantidade * preco_unitario)
            FROM itens_pedido WHERE pedido_id = pe.id), 0) AS subtotal,
            calcular_total_pedido(pe.id) AS total
        FROM pedidos pe WHERE pe.id = %s
    ''', (pedido_id,)).fetchone()
    if order is None:
        raise HTTPException(404, 'Pedido não encontrado')
    order['itens'] = connection.execute('''
        SELECT ip.produto_id, p.nome AS produto, ip.quantidade, ip.preco_unitario,
               ip.quantidade * ip.preco_unitario AS subtotal
        FROM itens_pedido ip JOIN produtos p ON p.id = ip.produto_id
        WHERE ip.pedido_id = %s ORDER BY ip.produto_id
    ''', (pedido_id,)).fetchall()
    return order


@app.get('/health')
def health(connection: Connection):
    connection.execute('SELECT 1').fetchone()
    return {'status': 'ok'}


@app.get('/categorias')
def list_categories(connection: Connection, limit: Limit = 100, offset: Offset = 0):
    return connection.execute('SELECT * FROM categorias ORDER BY id LIMIT %s OFFSET %s', (limit, offset)).fetchall()


@app.post('/categorias', status_code=201)
def create_category(body: CategoriaInput, connection: Connection):
    return connection.execute('INSERT INTO categorias (nome) VALUES (%s) RETURNING *', (body.nome,)).fetchone()


@app.get('/clientes')
def list_clients(connection: Connection, limit: Limit = 100, offset: Offset = 0):
    return connection.execute('SELECT * FROM clientes ORDER BY id LIMIT %s OFFSET %s', (limit, offset)).fetchall()


@app.post('/clientes', status_code=201)
def create_client(body: ClienteInput, connection: Connection):
    return connection.execute('''INSERT INTO clientes (nome, email, telefone) VALUES (%s, %s, %s)
        RETURNING *''', (body.nome, body.email, body.telefone)).fetchone()


@app.get('/produtos', response_model=list[Produto])
def list_products(connection: Connection, limit: Limit = 100, offset: Offset = 0):
    return connection.execute('SELECT * FROM produtos ORDER BY id LIMIT %s OFFSET %s', (limit, offset)).fetchall()


@app.post('/produtos', status_code=201, response_model=Produto)
def create_product(body: ProdutoInput, connection: Connection):
    return connection.execute('''INSERT INTO produtos (nome, preco, categoria_id)
        VALUES (%s, %s, %s) RETURNING *''', (body.nome, body.preco, body.categoria_id)).fetchone()


@app.get('/produtos/{produto_id}', response_model=Produto)
def get_product(produto_id: ResourceId, connection: Connection):
    product = connection.execute('SELECT * FROM produtos WHERE id = %s', (produto_id,)).fetchone()
    if product is None:
        raise HTTPException(404, 'Produto não encontrado')
    return product


@app.post('/produtos/{produto_id}/entradas', response_model=Produto)
def add_stock(produto_id: ResourceId, body: QuantidadeInput, connection: Connection):
    # Bloqueio também impede remoção do produto entre a consulta e a entrada.
    if connection.execute('SELECT id FROM produtos WHERE id = %s FOR UPDATE', (produto_id,)).fetchone() is None:
        raise HTTPException(404, 'Produto não encontrado')
    connection.execute('''INSERT INTO movimentacoes_estoque (produto_id, tipo, quantidade)
        VALUES (%s, 'entrada', %s)''', (produto_id, body.quantidade))
    return connection.execute('SELECT * FROM produtos WHERE id = %s', (produto_id,)).fetchone()


@app.post('/pedidos', status_code=201, response_model=Pedido)
def create_order(body: PedidoInput, connection: Connection):
    pedido_id = connection.execute('SELECT registrar_pedido(%s, %s, %s, %s) AS id', (
        body.cliente_id, Jsonb([item.model_dump() for item in body.itens]), body.desconto, body.frete,
    )).fetchone()['id']
    return read_order(connection, pedido_id)


@app.get('/pedidos', response_model=list[Pedido])
def list_orders(connection: Connection, limit: Limit = 100, offset: Offset = 0):
    ids = connection.execute('SELECT id FROM pedidos ORDER BY id LIMIT %s OFFSET %s', (limit, offset)).fetchall()
    return [read_order(connection, row['id']) for row in ids]


@app.get('/pedidos/{pedido_id}', response_model=Pedido)
def get_order(pedido_id: ResourceId, connection: Connection):
    return read_order(connection, pedido_id)


@app.post('/pedidos/{pedido_id}/cancelar', response_model=Pedido)
def cancel_order(pedido_id: ResourceId, connection: Connection):
    connection.execute('CALL cancelar_pedido(%s)', (pedido_id,))
    return read_order(connection, pedido_id)
