SELECT *
FROM pedidos
WHERE cliente_id = 1;

CREATE INDEX idx_pedidos_cliente
ON pedidos(cliente_id);

CREATE INDEX idx_produtos_categoria
ON produtos(categoria_id);

CREATE INDEX idx_itens_pedido_produto
ON itens_pedido(produto_id);

CREATE INDEX idx_pedidos_cliente
ON pedidos(cliente_id);