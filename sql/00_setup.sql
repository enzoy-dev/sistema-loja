-- =====================================================
-- Script de setup completo do Sistema de Loja
-- Execute este arquivo em um banco PostgreSQL limpo
-- =====================================================

\set ON_ERROR_STOP on
BEGIN;

\echo '>>> Criando schema...'
\ir 01_schema.sql

\echo '>>> Inserindo dados iniciais...'
\ir 02_inserts.sql

\echo '>>> Criando constraints e regras de integridade...'
\ir 13_integridade.sql
\ir 14_constraints.sql
\ir 31_status_pedido.sql
\ir 32_valores_pedido.sql

\echo '>>> Criando histórico de estoque...'
\ir 15_historico_estoque.sql

\echo '>>> Criando functions e triggers...'
\ir 16_functions.sql
\ir 17_funcoes_estoque.sql
\ir 18_trigger_estoque.sql
\ir 19_validacao_estoque.sql

\echo '>>> Criando procedures de negócio...'
\ir 33_registrar_pedido.sql
\ir 20_registrar_venda.sql
\ir 28_cancelar_pedido.sql

\echo '>>> Criando views e relatórios...'
\ir 07_views.sql
\ir 21_ranking_clientes.sql
\ir 22_dashboard.sql
\ir 23_vendas_categoria.sql
\ir 24_produtos_mais_vendidos.sql
\ir 25_produtos_sem_venda.sql
\ir 26_total_pedido.sql
\ir 27_produtos_estoque_baixo.sql
\ir 30_pedidos_detalhados.sql

\echo '>>> Criando histórico de status de pedidos...'
\ir 29_historico_status_pedido.sql

\echo '>>> Criando autenticação e sessões da API...'
\ir 34_autenticacao.sql

COMMIT;
\echo '>>> Setup finalizado com sucesso!'
