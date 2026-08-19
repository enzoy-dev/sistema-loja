SELECT *
FROM produtos;

SELECT
    nome,
    preco
FROM produtos;

SELECT
    nome,
    preco
FROM produtos
WHERE preco > 100;

SELECT
    nome,
    preco
FROM produtos
ORDER BY preco DESC;

SELECT
    nome,
    estoque
FROM produtos
WHERE estoque < 20;

SELECT
    nome,
    email,
    telefone
FROM clientes
ORDER BY nome;

SELECT *
FROM categorias;

SELECT
    nome,
    preco
FROM produtos
WHERE categoria_id = 1;

SELECT
    id,
    cliente_id,
    data_pedido,
    status
FROM pedidos
WHERE status = 'concluido';

SELECT
    pedido_id,
    SUM(quantidade * preco_unitario) AS total
FROM itens_pedido
GROUP BY pedido_id;

SELECT
    nome,
    estoque
FROM produtos
WHERE estoque BETWEEN 10 AND 50;

SELECT
    nome,
    preco
FROM produtos
WHERE preco <= 200
ORDER BY preco ASC;

SELECT
    COUNT(*) AS total_produtos
FROM produtos;

SELECT
    AVG(preco) AS preco_medio
FROM produtos;

SELECT
    nome,
    preco
FROM produtos
ORDER BY preco DESC
LIMIT 1;

SELECT
    nome,
    preco
FROM produtos
ORDER BY preco ASC
LIMIT 1;

SELECT
    SUM(estoque) AS estoque_total
FROM produtos;