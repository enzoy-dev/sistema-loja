SELECT
    nome,
    preco
FROM produtos
WHERE preco > (
    SELECT AVG(preco)
    FROM produtos
)
ORDER BY preco DESC;

SELECT
    nome,
    email
FROM clientes
WHERE id IN (
    SELECT cliente_id
    FROM pedidos
);

SELECT
    nome,
    preco,
    categoria_id
FROM produtos
WHERE preco > (
    SELECT AVG(p2.preco)
    FROM produtos p2
    WHERE p2.categoria_id = produtos.categoria_id
);

