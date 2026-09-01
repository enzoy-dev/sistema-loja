ALTER TABLE clientes
ADD CONSTRAINT uq_cliente_email
UNIQUE (email);

ALTER TABLE clientes
ADD CONSTRAINT chk_cliente_email
CHECK (email LIKE '%@%.%');

ALTER TABLE pedidos
ADD CONSTRAINT chk_pedido_status
CHECK (
    status IN ('pendente', 'concluido', 'cancelado')
);

ALTER TABLE pedidos
ALTER COLUMN data_pedido SET DEFAULT CURRENT_DATE;