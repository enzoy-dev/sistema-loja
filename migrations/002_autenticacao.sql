-- Aplicar uma única vez em um banco com a migração 001 já instalada.
\set ON_ERROR_STOP on
BEGIN;
\ir ../sql/34_autenticacao.sql
COMMIT;
