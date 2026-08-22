BEGIN;

UPDATE produtos
SET estoque = estoque - 1
WHERE id = 1;

INSERT INTO pedidos (
    id,
    cliente_id,
    data_pedido,
    status
)
VALUES (
    5,
    1,
    CURRENT_DATE,
    'pendente'
);

COMMIT;

BEGIN;

UPDATE produtos
SET estoque = estoque - 1
WHERE id = 2;

UPDATE produtos
SET estoque = estoque - 100000
WHERE id = 3;

ROLLBACK;