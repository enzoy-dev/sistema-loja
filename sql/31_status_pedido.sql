-- Evolução da constraint criada em 13_integridade.sql.
ALTER TABLE pedidos
DROP CONSTRAINT chk_pedido_status;

ALTER TABLE pedidos
ADD CONSTRAINT chk_pedido_status
CHECK (status IN ('pendente', 'concluido', 'cancelado', 'em_preparacao'));
