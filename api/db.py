import os

import psycopg
from psycopg.rows import dict_row


def get_connection():
    # DATABASE_URL ou variáveis PGHOST/PGPORT/PGUSER/PGPASSWORD/PGDATABASE.
    dsn = os.getenv('DATABASE_URL', '')
    options = {} if dsn or os.getenv('PGDATABASE') else {'dbname': 'sistema_loja'}
    with psycopg.connect(dsn, row_factory=dict_row, connect_timeout=5, **options) as connection:
        yield connection
