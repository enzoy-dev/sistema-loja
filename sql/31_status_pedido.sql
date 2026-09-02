ALTER TABLE pedidos
ADD CONSTRAINT chk_pedido_status
CHECK (status IN ('pendente', 'concluido', 'cancelado', 'em_preparacao'));