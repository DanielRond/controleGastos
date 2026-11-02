# Hospedagem

O controleGastos roda em dois modos com o mesmo código: **local** (só no seu computador) e **hospedado** (num servidor, em Docker). Os dados ficam num banco SQLite; a configuração vem só de variáveis de ambiente.

## Local

```bash
uv sync --extra web
(cd frontend && npm ci && npm run build)      # Node 24+
uv run controlegastos usuario criar ana       # pede a senha duas vezes (mínimo 8 caracteres)
uv run controlegastos web                     # http://127.0.0.1:8000
```

Os dados ficam em `dados/controlegastos.db` (ignorado pelo git). O login é exigido também no modo local.

## Hospedado com Docker

1. **Gere uma chave secreta** (assina o cookie de sessão; guarde-a, trocar a chave desconecta todo mundo):

   ```bash
   export CONTROLEGASTOS_CHAVE_SECRETA="$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')"
   ```

2. **Suba o serviço** com o `docker-compose.yml` do repositório:

   ```bash
   docker compose up -d --build
   ```

   O compose se recusa a subir sem a chave secreta. O app escuta em `127.0.0.1:8000` da máquina; a porta não fica aberta para a internet.

3. **Crie a sua conta** (não há cadastro público):

   ```bash
   printf '%s' 'sua-senha-longa' | docker compose exec -T controlegastos controlegastos usuario criar ana --senha-stdin
   ```

   Prefira digitar a senha de forma que ela não fique no histórico do shell (por exemplo, lendo de um arquivo com permissão restrita).

4. **Ponha HTTPS na frente.** Qualquer proxy reverso serve; com o Caddy, o `Caddyfile` mais curto é:

   ```text
   gastos.exemplo.com {
       reverse_proxy 127.0.0.1:8000
   }
   ```

   O Caddy obtém e renova o certificado sozinho. Com HTTPS, deixe `CONTROLEGASTOS_COOKIE_SECURE=1` (o padrão do compose) para o cookie só viajar criptografado.

### Variáveis de ambiente

| Variável | Para quê | Padrão |
|---|---|---|
| `CONTROLEGASTOS_CHAVE_SECRETA` | Assina o cookie de sessão. **Obrigatória** quando `COOKIE_SECURE=1`. | gerada por processo (só modo local) |
| `CONTROLEGASTOS_COOKIE_SECURE` | `1` quando o acesso é por HTTPS | `0` (no compose: `1`) |
| `DATABASE_URL` | Outro banco (ex.: Postgres). Sem ela, usa o SQLite do volume `/data`. | `sqlite:////data/controlegastos.db` |
| `CONTROLEGASTOS_DADOS` | Pasta do SQLite local | `dados` (na imagem: `/data`) |

Nenhum segredo está no repositório nem na imagem; a imagem roda sem root e só escreve em `/data`.

## Backup

Os dados estão no volume `/data`. Três formas, da mais simples à mais completa:

- **Pelo próprio app:** na tela *Arquivos*, **Exportar JSON** guarda tudo num arquivo que pode ser importado de volta. Faça isso de tempos em tempos e guarde fora do servidor.
- **Cópia do banco**, com o app parado ou usando o backup do SQLite:

  ```bash
  docker compose exec controlegastos python -c "import sqlite3; o=sqlite3.connect('/data/controlegastos.db'); d=sqlite3.connect('/data/backup.db'); o.backup(d)"
  docker compose cp controlegastos:/data/backup.db ./backup-$(date +%F).db
  ```

- **Volume inteiro:** `docker run --rm -v controlegastos_dados:/data -v "$PWD":/backup busybox tar czf /backup/dados.tgz -C /data .`

Para restaurar um JSON, use *Arquivos → Importar JSON* (meses que já existem pedem confirmação para substituir).

## Atualizar

```bash
git pull
docker compose up -d --build
```

As migrações do banco rodam sozinhas ao iniciar; os dados do volume são preservados. Para verificar o serviço: `curl http://127.0.0.1:8000/api/saude` deve devolver `{"status":"ok"}`.

## Segurança em resumo

- Login obrigatório, senhas com Argon2, cookie `HttpOnly` + `SameSite=Lax` (+ `Secure` em HTTPS), proteção contra CSRF e bloqueio de 15 minutos após 5 tentativas erradas.
- O bloqueio de tentativas é guardado na memória do processo: rode **uma** instância do app (suficiente para uso pessoal).
- Mantenha o servidor atualizado e não exponha a porta 8000 diretamente à internet.
