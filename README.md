# Sistema de Loja

Projeto de estudo com PostgreSQL e uma API Python/FastAPI para clientes, produtos, estoque e pedidos. Inclui pedidos com vários produtos, desconto e frete, cancelamento com devolução de estoque, histórico e relatórios.

## Requisitos

- PostgreSQL 17, com servidor em execução e `psql`/`createdb` no PATH.
- Python 3.12 e permissão para criar bancos para executar os testes.
- Configure `PGHOST`, `PGPORT`, `PGUSER` e, quando necessário, `PGPASSWORD` para sua conexão. Não salve senhas no repositório.

## Instalar o banco

Na raiz do projeto:

```bash
createdb sistema_loja
psql -X -v ON_ERROR_STOP=1 -d sistema_loja -f sql/00_setup.sql
```

Use um banco **novo e vazio**. O setup resolve os arquivos a partir do próprio diretório e executa tudo em uma transação. Se ocorrer um erro, interrompe e desfaz a instalação; não apaga nem reinicializa bancos existentes.

A demonstração inclui 4 categorias, 5 clientes, 7 produtos, 4 pedidos e 5 itens. O estoque da carga é o saldo inicial após os pedidos históricos; suas baixas não são reaplicadas e não geram movimentos retroativos.

### Atualizar um banco da versão anterior

Se o banco já foi instalado com a versão que corrigiu a carga inicial, mas ainda não tem desconto, frete e pedidos com vários itens, faça um backup e aplique **uma única vez**:

```bash
pg_dump -Fc sistema_loja > sistema_loja_antes_checkout.dump
psql -X -v ON_ERROR_STOP=1 -d sistema_loja -f migrations/001_pedidos_multiplos.sql
```

A migração preserva dados e atribui desconto e frete zero aos pedidos existentes. Ela também é transacional. Não execute essa migração depois de uma instalação nova: o setup já inclui essas mudanças. Um banco deixado parcialmente instalado por versões com erro precisa ser investigado; não use a migração para completar uma instalação parcial.

## Iniciar a API

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
export PGDATABASE=sistema_loja
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload
```

A API aceita as variáveis padrão `PG*` do PostgreSQL. Como alternativa, configure `DATABASE_URL` no ambiente; ela tem prioridade sobre `PGDATABASE` na API. Sem essas duas opções, o nome padrão é `sistema_loja`. Não há carregamento automático de `.env`.

A documentação interativa está na rota `/docs`, e o esquema OpenAPI em `/openapi.json`. A rota `/health` consulta o banco para verificar a conexão.

A API foi preparada para desenvolvimento local. Ainda não possui autenticação nem autorização; mantenha o acesso local até adicionar essas funcionalidades antes de hospedar para terceiros.

### Rotas

| Método | Rota | Função |
| --- | --- | --- |
| GET | `/health` | Verificar a conexão com o banco |
| GET / POST | `/categorias` | Listar / cadastrar categorias |
| GET / POST | `/clientes` | Listar / cadastrar clientes |
| GET / POST | `/produtos` | Listar / cadastrar produtos |
| GET | `/produtos/{id}` | Consultar produto e estoque |
| POST | `/produtos/{id}/entradas` | Adicionar estoque e registrar histórico |
| GET / POST | `/pedidos` | Listar / registrar pedidos |
| GET | `/pedidos/{id}` | Consultar pedido, itens e total |
| POST | `/pedidos/{id}/cancelar` | Cancelar e devolver todos os itens ao estoque |

As listagens aceitam `limit` (1 a 100, padrão 100) e `offset` (a partir de zero). Produtos novos começam com estoque zero; use a rota de entradas com `{"quantidade": 10}` para abastecer.

### Exemplo de pedido

Com os dados iniciais:

```bash
curl --fail-with-body -X POST http://127.0.0.1:8000/pedidos \
  -H 'Content-Type: application/json' \
  -d '{"cliente_id":1,"itens":[{"produto_id":2,"quantidade":2},{"produto_id":3,"quantidade":1}],"desconto":"20.00","frete":"15.00"}'
```

O subtotal é R$ 399,70 e o total é R$ 394,70. Use o `id` retornado para consultar ou cancelar o pedido; não suponha um ID fixo, pois as sequências podem ter avançado.

## Regras de negócio

- Cada item precisa ter produto e quantidade inteira positiva. Produtos repetidos no mesmo pedido são rejeitados.
- O preço vem do cadastro do produto, fica registrado no item e não muda quando o preço do catálogo é alterado.
- **Total = soma dos itens − desconto + frete.** Desconto e frete são valores fixos em reais por pedido, opcionais e com padrão zero. Não são percentuais.
- Valores monetários usam `NUMERIC`/`Decimal`, com até duas casas decimais. A API retorna esses valores como strings decimais para preservar precisão.
- O desconto não pode superar o subtotal. Frete não pode ser negativo. Um desconto igual ao subtotal é permitido. O total máximo é R$ 99.999.999,99.
- O pedido inteiro é atômico: se qualquer item falhar, não ficam pedido, itens ou movimentos parciais.
- Produtos são bloqueados em ordem de ID durante a transação para evitar disputa da última unidade e deadlocks entre pedidos com produtos em ordens diferentes.
- Só pedidos concluídos podem ser cancelados. O cancelamento devolve todos os itens uma única vez e registra a mudança de status.
- A API limita pedidos a 100 itens. Erros de formato retornam 422, recursos ausentes 404 e conflitos de negócio, como estoque insuficiente ou cancelamento repetido, 409.

### Uso direto pelo SQL

```sql
SELECT registrar_pedido(
    1,
    '[{"produto_id":2,"quantidade":2},{"produto_id":3,"quantidade":1}]'::jsonb,
    20.00,
    15.00
) AS pedido_criado \gset
SELECT calcular_total_pedido(:pedido_criado);
CALL cancelar_pedido(:pedido_criado);
```

O procedimento antigo `CALL registrar_venda(1, 2, 2)` continua funcionando, com desconto e frete zero. Finalize transações abertas com `COMMIT` ou `ROLLBACK` para liberar os bloqueios. Alterações diretas nas tabelas podem contornar as regras dos procedimentos; o projeto não inclui uma política de permissões para impedir isso.

### Relatórios

```sql
SELECT * FROM dashboard_loja;
SELECT * FROM pedidos_detalhados;
SELECT * FROM produtos_estoque_baixo(20);
```

O faturamento do dashboard considera desconto e frete apenas dos pedidos concluídos. `pedidos_detalhados` mostra o total do pedido em cada linha; não some essa coluna entre os itens. Os exemplos de ranking por cliente, vendas por categoria e por produto continuam mostrando valores brutos dos itens, sem rateio do desconto/frete do pedido.

## Testes

Instale as dependências de desenvolvimento:

```bash
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
```

### Regressão SQL

```bash
createdb sistema_loja_testes
psql -X -v ON_ERROR_STOP=1 -d sistema_loja_testes -f sql/00_setup.sql
psql -X -v ON_ERROR_STOP=1 -d sistema_loja_testes -f tests/regressao.sql
```

Esse teste pressupõe a carga original. Faz `ROLLBACK` das mudanças, mas as sequências de IDs podem avançar.

### API e pedidos com vários itens

```bash
python -m pytest -q
```

Os testes usam PostgreSQL real, criam um banco exclusivo com nome aleatório e o removem ao terminar. Validam cadastro, entrada de estoque, valores monetários, pedidos com vários itens, cancelamento e atomicidade, inclusive uma falha simulada durante a gravação dos movimentos. Exigem permissão para criar e remover o próprio banco temporário.

Os testes usam as variáveis `PG*` para conexão administrativa (banco `postgres`, ou `PGDATABASE` se definido); não usam `DATABASE_URL`. A dependência de conexão da API é substituída para direcionar cada chamada ao banco exclusivo dos testes. Nenhum teste precisa acessar seu banco de trabalho.

### Concorrência

```bash
python tests/concorrencia.py
python tests/concorrencia.py --multiplos
```

Ambos criam e removem um banco próprio. O primeiro disputa a última unidade de um produto; o segundo disputa dois produtos enviados em ordens opostas. Uma venda deve passar e a outra falhar por estoque insuficiente, sem pedidos parciais nem estoque negativo.

### GitHub Actions

O workflow [Database tests](.github/workflows/database-tests.yml) executa em pushes e Pull Requests, e pode ser iniciado manualmente pela aba **Actions**. Ele inicia PostgreSQL 17 descartável, instala o banco e executa os testes SQL, de concorrência e da API. Não exige secrets: a senha no workflow pertence apenas ao banco temporário.

Para impedir merges quando houver falhas, configure a proteção da branch `main` e exija a verificação `database-tests`. O workflow sozinho não impede merges.

## Organização

- `sql/00_setup.sql`: ordem oficial de instalação; não execute todos os arquivos SQL como migrações.
- `sql/32_valores_pedido.sql` e `sql/33_registrar_pedido.sql`: valores financeiros e pedido com vários itens.
- `migrations/`: atualização explícita de bancos da versão anterior.
- `api/`: rotas, validação de entrada e conexão PostgreSQL.
- `tests/`: regressão SQL, integração com banco real e concorrência.
- `sql/03` a `sql/06` e `sql/08` a `sql/12`: exemplos e exercícios fora do setup. Alguns alteram dados.

Consulte [a estrutura do banco](docs/estrutura.md).
