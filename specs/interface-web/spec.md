---
capacidade: interface-web
codigo: WEB
status: vigente
---

# Capacidade: interface web

## Objetivo

Usar o controle de gastos de forma prática, sem editar JSON: entrar com login, registrar e corrigir lançamentos, ver o mês e o ano em painéis e baixar planilha e CSV. A CLI foi o ponto de partida e continua existindo. **Vigente: cada requisito tem teste.**

## Decisões tomadas

- Front-end **SPA** (opção B), separada da API; sem Streamlit.
- Back-end **FastAPI**; dados em SQLite (ver `armazenamento`).
- Deve rodar **localmente e hospedado**, com a mesma base de código.
- Autenticação com login; sem cadastro público na v1.
- Importação de extratos fica para depois da v1.
- Front-end: **React + TypeScript + Vite** (confirmado).
- O login é exigido também no modo local, para ser igual ao hospedado (confirmado).
- Uma pessoa usa na v1, mas o esquema já suporta vários usuários (confirmado).
- Exclusão por **lixeira** com restauração, esvaziada só manualmente (confirmado).
- Escopo da v1 confirmado: login, CRUD de lançamentos, painéis do mês e do ano, downloads, importar/exportar JSON.

## Comportamento

As telas estão em [specs/frontend](../frontend/spec.md) (WEB-18 e WEB-20 a 27) e a API em [specs/api](../api/spec.md). Aqui ficam só os requisitos de execução, da Fase 5.

Execução:

- **WEB-14** Modo local: `uv run controlegastos web` sobe API e front compilado no mesmo processo e origem (uvicorn), ligado a `127.0.0.1` na porta 8000 (`--porta` e `--host` mudam), com SQLite local em `dados/` (ou `DATABASE_URL`). Aplica as migrações ao iniciar, imprime o endereço e continua exigindo login. Sem o front compilado avisa e serve só a API. Ligar a um endereço que não seja de loopback sem `CONTROLEGASTOS_COOKIE_SECURE=1` imprime um aviso sobre HTTPS.
- **WEB-15** Modo hospedado: uma imagem Docker de dois estágios (Node compila o front; Python 3.14 roda o app), sem rodar como root, com dados em volume (`/data`), verificação de saúde em `/api/saude`, configuração só por variáveis de ambiente (`DATABASE_URL`, `CONTROLEGASTOS_CHAVE_SECRETA`, `CONTROLEGASTOS_COOKIE_SECURE`) e nenhum segredo no repositório nem na imagem. Há um `docker-compose.yml` de exemplo que exige a chave secreta e a documentação em `docs/hospedagem.md` (HTTPS por proxy reverso, criação da conta, backup e atualização). `.dockerignore` mantém dados, banco e `node_modules` fora da imagem.

## Fora de escopo (v1)

- Importação de extratos bancários, várias moedas, categorias personalizadas, app mobile, cadastro público, recuperação de senha por e-mail.

## Perguntas abertas

Nenhuma pendente.

## Rastreabilidade

Ver `design.md` e `tasks.md` desta pasta. Testes: `tests/test_api_front.py` e `tests/test_web_comando.py` (WEB-14), `tests/test_hospedagem.py` e `scripts/testar_imagem.py` (WEB-15, este também no CI).
