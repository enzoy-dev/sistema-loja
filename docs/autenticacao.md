# Autenticação e permissões da equipe

Contas internas da equipe são separadas dos clientes comerciais. Não há cadastro
público nem senha de administrador predefinida. Para hospedar, configure HTTPS,
acesso ao PostgreSQL e segredos da infraestrutura; adicionar login não faz o deploy.

## Instalação e migração

Um banco novo recebe autenticação em `sql/00_setup.sql`. Para um banco existente
que já possui pedidos com múltiplos itens, faça um backup e aplique uma única vez:

```bash
pg_dump -Fc sistema_loja > sistema_loja_antes_auth.dump
psql -X -v ON_ERROR_STOP=1 -d sistema_loja -f migrations/002_autenticacao.sql
```

A migração é aditiva e transacional: preserva pedidos/estoque e não cria contas.
Não a aplique após um setup novo. Se seu banco é anterior aos pedidos múltiplos,
aplique primeiro a migração `001`, seguindo as instruções do README.

## Primeiro administrador

Configure a conexão com `PG*` ou `DATABASE_URL`, como na API. No PowerShell,
após definir as demais variáveis da conexão:

```powershell
$env:PGDATABASE = "sistema_loja"
python -m api.manage create-user --login enzo --role admin
```

A CLI pede senha e confirmação sem exibi-las: use de 12 a 128 caracteres. Não
há contas instaladas por padrão. O login aceita de 3 a 64 letras minúsculas,
números, pontos, hífens ou underscores. Não forneça senhas como argumentos nem
as salve no código. Esse comando é destinado
a quem administra a máquina/banco; não é uma rota pública. Outras contas podem
ser criadas pela CLI ou por `POST /auth/usuarios` autenticado como administrador.

## Login pelo Swagger ou PowerShell

No `/docs`, execute `POST /auth/login` com `login` e `senha`. Copie `access_token`
para **Authorize → HTTPBearer** e execute uma rota permitida. Ao terminar, use
`POST /auth/logout`.

Também é possível usar PowerShell sem gravar a senha no histórico:

```powershell
$credencial = Get-Credential -UserName enzo -Message "Login da API local"
$body = @{ login = $credencial.UserName; senha = $credencial.GetNetworkCredential().Password } | ConvertTo-Json
$sessao = Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/auth/login" -ContentType "application/json" -Body $body
$headers = @{ Authorization = "Bearer $($sessao.access_token)" }
Invoke-RestMethod -Uri "http://127.0.0.1:8000/produtos" -Headers $headers
```

O login transmite a senha ao servidor, por isso conexões externas exigem HTTPS.
Não compartilhe o token: ele autoriza operações enquanto estiver válido.

## Permissões

| Operação | leitor | vendedor | admin |
| --- | --- | --- | --- |
| Consultar categorias, clientes, produtos e pedidos | Sim | Sim | Sim |
| Cadastrar clientes e registrar pedidos | Não | Sim | Sim |
| Cadastrar categorias/produtos e adicionar estoque | Não | Não | Sim |
| Cancelar pedidos | Não | Não | Sim |
| Listar/criar usuários e alterar acesso de outro usuário | Não | Não | Sim |
| Consultar sua identidade e encerrar sua sessão | Sim | Sim | Sim |

São públicos `/health`, `/docs`, `/openapi.json` e `/auth/login`. Sem sessão válida,
as demais rotas retornam `401`; sem permissão, `403`. O leitor é um funcionário
com leitura da loja inteira, incluindo clientes. Não há isolamento por cliente.

## Senhas, sessões e limitações

- PBKDF2-HMAC-SHA256, 600.000 iterações e salt aleatório por senha.
- Tokens opacos com 32 bytes aleatórios; só seu SHA-256 fica no PostgreSQL.
- Validade de 60 minutos; `LOJA_SESSION_TTL_MINUTES` aceita de 1 a 1.440 minutos.
- Cada requisição consulta sessão e perfil atual. Rebaixar um perfil afeta as
  próximas requisições, inclusive as que usam tokens já emitidos.
- Logout revoga a sessão atual. Desativar uma conta remove todas as suas sessões.
- A rota administrativa impede alterar o próprio perfil/acesso, evitando remover
  acidentalmente o último administrador ativo. Alterações de perfil são serializadas
  e revalidam o administrador após a espera, inclusive em mudanças simultâneas.
- Cinco falhas na mesma conta em 15 minutos causam bloqueio temporário. O contador
  persiste no banco e também vale para logins desconhecidos. Ele não substitui
  limites por IP na borda: terceiros podem provocar um bloqueio temporário de conta.
- Não há MFA, cadastro público nem recuperação de senha por e-mail.

Para trocar uma senha e revogar todas as sessões da conta:

```bash
python -m api.manage reset-password --login enzo
```

O comando também limpa o bloqueio de tentativas. Hashes de senha/sessão não são
retornados nas rotas de usuários. Contas fixas dos testes só existem nos bancos
descartáveis, não na instalação normal.

## Validação

Os testes com PostgreSQL real cobrem tokens adulterados/expirados, logout, perfis,
desativação, alteração de permissão de uma sessão existente, limite de login e
preservação de pedidos durante a migração. As regras de vendas e concorrência
continuam cobertas pelos testes SQL e pela API.
