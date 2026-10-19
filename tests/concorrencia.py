"""Teste com duas conexões psql; usa e remove um banco temporário próprio."""
from concurrent.futures import ThreadPoolExecutor
import argparse
import os
from pathlib import Path
import subprocess
import time
import uuid

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--multiplos', action='store_true', help='Disputar dois produtos em ordens opostas')
MULTIPLOS = parser.parse_args().multiplos
ROOT = Path(__file__).resolve().parents[1]
DATABASE = 'loja_teste_' + uuid.uuid4().hex[:12]


def sql(command, *, appname=None):
    return subprocess.run(
        ['psql', '-X', '-v', 'ON_ERROR_STOP=1', '-At', '-d', DATABASE, '-c', command],
        env={**os.environ, **({'PGAPPNAME': appname} if appname else {})},
        text=True, capture_output=True, timeout=15, check=True,
    ).stdout.strip()


first = second = None
subprocess.run(['createdb', DATABASE], check=True, timeout=15)
try:
    subprocess.run(
        ['psql', '-X', '-v', 'ON_ERROR_STOP=1', '-d', DATABASE,
         '-f', str(ROOT / 'sql/00_setup.sql')],
        check=True, capture_output=True, text=True, timeout=30,
    )
    sql('UPDATE produtos SET estoque = 1 WHERE id IN (2, 3)' if MULTIPLOS else
        'UPDATE produtos SET estoque = 1 WHERE id = 2')
    first_sale = 'CALL registrar_venda(1, 2, 1)'
    second_sale = first_sale
    if MULTIPLOS:
        first_sale = '''SELECT registrar_pedido(1, '[{"produto_id":2,"quantidade":1},{"produto_id":3,"quantidade":1}]')'''
        second_sale = '''SELECT registrar_pedido(1, '[{"produto_id":3,"quantidade":1},{"produto_id":2,"quantidade":1}]')'''
    first = subprocess.Popen(
        ['psql', '-X', '-v', 'ON_ERROR_STOP=1', '-At', '-d', DATABASE],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    # A primeira venda fica aberta e segura o bloqueio da última unidade.
    first.stdin.write('BEGIN; ' + first_sale + ';\n\\echo PRONTO\n')
    first.stdin.flush()
    # readline pode armazenar linhas; um thread permite impor o prazo total.
    def aguardar_primeira_venda():
        for line in first.stdout:
            if line.strip() == 'PRONTO':
                return
        raise RuntimeError('Primeira conexão terminou antes da venda')
    executor = ThreadPoolExecutor(max_workers=1)
    ready = executor.submit(aguardar_primeira_venda)
    try:
        ready.result(timeout=15)
    finally:
        if not ready.done():
            first.kill()
        executor.shutdown(wait=True)
    second = subprocess.Popen(
        ['psql', '-X', '-v', 'ON_ERROR_STOP=1', '-At', '-d', DATABASE,
         '-c', "SET lock_timeout = '10s'; " + second_sale],
        env={**os.environ, 'PGAPPNAME': DATABASE + '_segunda'},
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    deadline = time.monotonic() + 8
    while sql("SELECT count(*) FROM pg_stat_activity WHERE application_name = '"
               + DATABASE + "_segunda' AND cardinality(pg_blocking_pids(pid)) > 0") != '1':
        if time.monotonic() >= deadline or second.poll() is not None:
            raise RuntimeError('Segunda venda não aguardou o bloqueio esperado')
        time.sleep(0.05)
    first.stdin.write('COMMIT;\n\\q\n')
    first.stdin.flush()
    first.wait(timeout=15)
    assert first.returncode == 0, first.stderr.read()
    _, errors = second.communicate(timeout=15)
    assert second.returncode != 0 and 'Estoque insuficiente' in errors, errors
    assert sql('SELECT estoque FROM produtos WHERE id = 2') == '0'
    assert sql('SELECT count(*) FROM pedidos') == '5'
    assert sql('SELECT count(*) FROM movimentacoes_estoque') == ('2' if MULTIPLOS else '1')
    if MULTIPLOS:
        assert sql('SELECT estoque FROM produtos WHERE id = 3') == '0'
    print('Concorrência passou: uma venda confirmada; a segunda rejeitada sem estoque negativo.')
finally:
    for process in (first, second):
        if process is not None:
            if process.poll() is None:
                process.kill()
            process.communicate(timeout=15)
    subprocess.run(['dropdb', '--force', DATABASE], check=True, timeout=15)
