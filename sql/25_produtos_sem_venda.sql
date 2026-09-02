SELECT
    p.id,
    p.nome,
    p.preco,
    p.estoque
FROM produtos p
LEFT JOIN itens_pedido ip
    ON p.id = ip.produto_id
WHERE ip.id IS NULL
ORDER BY p.estoque DESC;