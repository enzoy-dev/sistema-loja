-- =====================================================
-- Script de setup completo do Sistema de Loja
-- Execute este arquivo em um banco PostgreSQL limpo
-- =====================================================

\echo '>>> Criando schema...'
\i 01_schema.sql

\echo '>>> Inserindo dados iniciais...'
\i 02_inserts.sql

\echo '>>> Criando constraints e regras de integridade...'
\i 13_integridade.sql
\i 14_constraints.sql

\echo '>>> Criando histórico de estoque...'
\i 15_historico_estoque.sql

\echo '>>> Criando functions e triggers...'
\i 16_functions.sql
\i 17_funcoes_estoque.sql
\i 18_trigger_estoque.sql
\i 19_validacao_estoque.sql

\echo '>>> Criando procedures de negócio...'
\i 20_registrar_venda.sql
\i 28_cancelar_pedido.sql

\echo '>>> Criando views e relatórios...'
\i 07_views.sql
\i 21_ranking_clientes.sql
\i 22_dashboard.sql
\i 23_vendas_categoria.sql
\i 24_produtos_mais_vendidos.sql
\i 25_produtos_sem_venda.sql
\i 26_total_pedido.sql
\i 27_produtos_estoque_baixo.sql
\i 30_pedidos_detalhados.sql

\echo '>>> Criando histórico de status de pedidos...'
\i 29_historico_status_pedido.sql

\echo '>>> Setup finalizado com sucesso!'