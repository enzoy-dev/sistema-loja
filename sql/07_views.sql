CREATE VIEW relatorio_vendas AS
SELECT
    pedidos.id AS pedido,
    clientes.nome AS cliente,
    produtos.nome AS produto,
    itens_pedido.quantidade,
    itens_pedido.preco_unitario,
    itens_pedido.quantidade * itens_pedido.preco_unitario AS subtotal,
    pedidos.data_pedido,
    pedidos.status
FROM itens_pedido
JOIN pedidos
    ON itens_pedido.pedido_id = pedidos.id
JOIN clientes
    ON pedidos.cliente_id = clientes.id
JOIN produtos
    ON itens_pedido.produto_id = produtos.id;