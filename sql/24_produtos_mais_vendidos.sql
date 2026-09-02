SELECT
    p.nome AS produto,
    SUM(ip.quantidade) AS unidades_vendidas,
    SUM(ip.quantidade * ip.preco_unitario) AS faturamento
FROM produtos p
JOIN itens_pedido ip
    ON p.id = ip.produto_id
JOIN pedidos pe
    ON ip.pedido_id = pe.id
WHERE pe.status = 'concluido'
GROUP BY p.id, p.nome
ORDER BY unidades_vendidas DESC;