CREATE OR REPLACE VIEW pedidos_detalhados AS
SELECT
    pe.id AS pedido_id,
    c.nome AS cliente,
    pe.data_pedido,
    pe.status,
    p.nome AS produto,
    ip.quantidade,
    ip.preco_unitario,
    ip.quantidade * ip.preco_unitario AS subtotal
FROM pedidos pe
JOIN clientes c
    ON pe.cliente_id = c.id
JOIN itens_pedido ip
    ON pe.id = ip.pedido_id
JOIN produtos p
    ON ip.produto_id = p.id;