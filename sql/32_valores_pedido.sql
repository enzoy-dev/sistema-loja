-- Valores monetários em reais: desconto fixo e frete por pedido.
ALTER TABLE pedidos
    ADD COLUMN desconto NUMERIC(10,2) NOT NULL DEFAULT 0,
    ADD COLUMN frete NUMERIC(10,2) NOT NULL DEFAULT 0,
    ADD CONSTRAINT chk_pedido_desconto CHECK (desconto >= 0 AND desconto < 'Infinity'::numeric),
    ADD CONSTRAINT chk_pedido_frete CHECK (frete >= 0 AND frete < 'Infinity'::numeric);
