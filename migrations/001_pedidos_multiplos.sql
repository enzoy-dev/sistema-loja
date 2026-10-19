-- Aplicar uma vez sobre a versão anterior já instalada do projeto.
\set ON_ERROR_STOP on
BEGIN;
\ir ../sql/32_valores_pedido.sql
\ir ../sql/33_registrar_pedido.sql
\ir ../sql/20_registrar_venda.sql
\ir ../sql/28_cancelar_pedido.sql
\ir ../sql/22_dashboard.sql
\ir ../sql/26_total_pedido.sql
\ir ../sql/30_pedidos_detalhados.sql
COMMIT;
