UPDATE produtos
SET preco = preco * 1.10
WHERE categoria_id = 1;

UPDATE produtos
SET preco = 0;

UPDATE produtos
SET estoque = estoque - 2
WHERE id = 2;

SELECT
    nome,
    estoque
FROM produtos
WHERE estoque < 20;

UPDATE pedidos
SET status = 'concluido'
WHERE id = 3;

DELETE FROM clientes
WHERE id = 5;

