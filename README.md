# Sistema de Loja

Projeto de estudo de SQL e modelagem de banco de dados com PostgreSQL. Inclui clientes, produtos, pedidos, controle de estoque, procedimentos de venda e cancelamento, histórico de alterações e relatórios.

## Requisitos

- PostgreSQL 17 (versão usada na validação), com `psql` e `createdb` no PATH.
- Servidor PostgreSQL em execução e usuário com permissão para criar bancos.
- Python 3 para o teste opcional de concorrência, sem pacotes adicionais.

Os comandos usam a conexão padrão do PostgreSQL. Se necessário, configure `PGHOST`, `PGPORT` e `PGUSER` para o seu servidor.

## Instalação

Na raiz do repositório:

```bash
createdb sistema_loja
psql -X -v ON_ERROR_STOP=1 -d sistema_loja -f sql/00_setup.sql
```

Use um banco **novo e vazio**. O script encontra os arquivos em relação ao próprio diretório, interrompe na primeira falha e executa toda a instalação em uma transação. Se houver erro, o PostgreSQL desfaz as alterações dessa execução. Ele não apaga nem reinicializa um banco existente.

A carga inclui 4 categorias, 5 clientes, 7 produtos, 4 pedidos e 5 itens. São dados fictícios para estudo; o produto 7 é um jogo de tabuleiro, usado pelo pedido 2. Os estoques da carga representam o saldo inicial de demonstração após os pedidos históricos; a carga não reaplica suas baixas nem gera movimentos retroativos.

Confira os resultados:

```bash
psql -d sistema_loja -c 'SELECT * FROM dashboard_loja;'
psql -d sistema_loja -c 'SELECT * FROM pedidos_detalhados;'
```

## Venda e cancelamento

O procedimento `registrar_venda(cliente_id, produto_id, quantidade)` cria um pedido concluído com um item e registra a saída do estoque. Cada chamada representa uma venda de um produto; pedidos com vários produtos não possuem um procedimento próprio.

Exemplo em `psql -d sistema_loja`:

```sql
SELECT id, nome, preco, estoque FROM produtos WHERE id = 2;
CALL registrar_venda(1, 2, 2);
SELECT id AS pedido_vendido FROM pedidos ORDER BY id DESC LIMIT 1 \gset
SELECT calcular_total_pedido(:pedido_vendido);
SELECT estoque FROM produtos WHERE id = 2;
CALL cancelar_pedido(:pedido_vendido);
SELECT estoque FROM produtos WHERE id = 2;
SELECT * FROM historico_status_pedido WHERE pedido_id = :pedido_vendido;
```

O exemplo usa uma sessão sem outras vendas simultâneas para identificar o pedido recém-criado. O cancelamento aceita apenas pedidos concluídos e devolve as quantidades ao estoque uma única vez. Quantidades nulas, zero ou negativas, clientes/produtos inexistentes e vendas sem estoque são rejeitados. O produto fica bloqueado durante a transação para serializar vendas concorrentes; mantenha transações curtas e finalize com `COMMIT` ou `ROLLBACK`.

Relatórios adicionais:

```sql
SELECT * FROM dashboard_loja;
SELECT * FROM produtos_estoque_baixo(20);
SELECT * FROM pedidos_detalhados;
```

## Testes

Execute a regressão em um banco recém-instalado, separado dos seus dados de trabalho:

```bash
createdb sistema_loja_testes
psql -X -v ON_ERROR_STOP=1 -d sistema_loja_testes -f sql/00_setup.sql
psql -X -v ON_ERROR_STOP=1 -d sistema_loja_testes -f tests/regressao.sql
```

A regressão verifica a carga, views, totais, venda, baixa de estoque, cancelamento, devolução, histórico, status `em_preparacao` e rejeição de operações inválidas sem registros parciais. As alterações de dados são desfeitas com `ROLLBACK`; sequências de IDs podem avançar. O teste pode ser repetido nesse banco, mas pressupõe a carga original.

Para testar duas vendas simultâneas da última unidade:

```bash
python3 tests/concorrencia.py
```

Esse teste cria um banco com nome único, instala o projeto, verifica o bloqueio entre duas conexões e remove apenas o banco que criou. Exige permissão para criar e remover esse banco. Uma venda deve passar e a outra deve falhar por estoque insuficiente.

## Organização dos scripts

- `sql/00_setup.sql`: ponto de entrada e ordem oficial de instalação.
- Schema, carga, constraints, funções, triggers, procedimentos e views: incluídos pelo setup conforme suas dependências.
- `sql/31_status_pedido.sql`: substitui a constraint anterior e acrescenta `em_preparacao`; já faz parte do setup.
- `sql/03` a `sql/06`, `sql/08` a `sql/12`: exemplos de consultas e exercícios, fora da instalação. Alguns modificam dados; não execute todos os arquivos em sequência como migrações.
- `tests/`: regressão de regras de negócio e teste de concorrência.

Consulte [a estrutura do banco](docs/estrutura.md). O projeto oferece rotinas SQL; não inclui interface web nem uma camada de permissões que impeça alterações diretas nas tabelas. Use os procedimentos para os fluxos de venda e cancelamento.
