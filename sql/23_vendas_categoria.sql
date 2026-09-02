SELECT
    c.nome AS categoria,
    COUNT(DISTINCT p.id) AS produtos_vendidos,
    SUM(ip.quantidade) AS quantidade_vendida,
    SUM(ip.quantidade * ip.preco_unitario) AS faturamento
FROM categorias c
JOIN produtos p
    ON c.id = p.categoria_id
JOIN itens_pedido ip
    ON p.id = ip.produto_id
JOIN pedidos pe
    ON ip.pedido_id = pe.id
WHERE pe.status = 'concluido'
GROUP BY c.id, c.nome
ORDER BY faturamento DESC;