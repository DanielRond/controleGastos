# Plano: interface web

## Retomada (para qualquer agente ou provedor)

Atualize esta seção a cada passo concluído, junto do commit.

- **Estado**: Fases 1 a 4 concluídas (4d na branch `feat/fase4d-e2e`, a mesclar). Resta a Fase 5: execução local (`controlegastos web`) e hospedada (Docker).
- **Branch atual**: `feat/fase4d-e2e`.
- **Último passo concluído**: 4d. A API serve o front compilado (fallback de SPA, sem leitura fora da pasta); `scripts/servidor_e2e.py`; 20 testes Playwright em Chromium real (login, mês, ano com gráficos desenhados, downloads, importação, lixeira, teclado); job `e2e` no CI; spec `frontend` vigente. O E2E achou 3 problemas reais que os testes de componente não pegavam (categoria que vazava para o próximo lançamento, formulário limpo no meio da digitação, aviso de "salvo" que sumia); todos corrigidos.
- **Próximo passo**: Fase 5. (5.1) comando `controlegastos web` (uvicorn em 127.0.0.1, porta configurável, mesmo processo e origem, SQLite local em `dados/`, migrações no start, aviso se o front não foi compilado) com testes citando WEB-14; (5.2) `Dockerfile` em dois estágios (Node 24 compila o front; Python 3.14 instala com `uv sync --extra web --no-dev` e roda uvicorn), `docker-compose.yml` de exemplo com volume para o SQLite, leitura de `DATABASE_URL`, `CONTROLEGASTOS_CHAVE_SECRETA` e `CONTROLEGASTOS_COOKIE_SECURE`, criação de conta por `docker run ... usuario criar`, testes do WEB-15 e documentação de hospedagem (HTTPS por proxy reverso, backup do SQLite, exportar JSON); promover `interface-web` a `vigente`; (5.3) atualizar AGENTS.md, README e hooks.
- **Node**: `export PATH=$HOME/.local/share/node/node-v24.22.2-linux-x64/bin:$PATH` (o do sistema é o 18). Docker 29 está instalado para testar a imagem.
- **Como retomar**: `git checkout main && git pull`; ler `AGENTS.md`, este arquivo, `design.md` e os specs; criar a branch da tarefa; spec primeiro, testes antes do código, `uv run ruff check . --no-cache`, `uv run pytest` e `uv run python scripts/conferir_specs.py` verdes antes de cada commit; abrir PR e mesclar com o CI verde.
- **Ambiente**: Python 3.14 via uv; Docker disponível; Node 18 no sistema (a Fase 4 exige Node 20+, instalar com fnm).

Cada fase é um PR pequeno, com spec primeiro, testes antes do código e revisão humana. Os status `rascunho` passam a `vigente` quando a fase correspondente começar (aí o CI exige um teste por requisito).

- [x] **Fase 0 — Decisões**: perguntas abertas respondidas e specs aprovados pelo usuário.
- [x] **Fase 1 — Serviço (sem mudar comportamento)** (LAN-07, PLN-12, PLN-13, EXP-12)
  - [x] 1.1 Extrair `servico.py` e `resumo.py` (dados dos gráficos públicos); CLI chama o serviço
  - [x] 1.2 Geração do `.xlsx` e dos CSV em memória (bytes)
  - Critério cumprido: suíte existente verde; saída idêntica à anterior (CSV byte a byte, `.xlsx` célula a célula).
- [x] **Fase 2 — Armazenamento** (STO-01 a STO-14, VAL-13)
  - [x] 2.1 Extra `web` com instalação real da stack em Python 3.14; `armazenamento` vigente
  - [x] 2.2 Repositório por usuário, carga para `LivroCaixa`, isolamento (STO-06)
  - [x] 2.3 Importar/exportar JSON transacional (recusa mês existente; `substituir` explícito), valor com no máximo 2 casas (STO-11) e `controlegastos banco atualizar`
  - [x] 2.4 Exclusão lógica e lixeira no repositório (STO-12, STO-13), com os testes de propriedade do design
- [x] **Fase 3 — API e autenticação** (spec `api`: WEB-01 a 13, 16, 17, 19)
  - [x] 3.1 App FastAPI, sessão, login, CSRF, limite de tentativas, `controlegastos usuario criar`
  - [x] 3.2 Rotas de meses e lançamentos com erros `{caminho, mensagem}`
  - [x] 3.3 Resumo anual, downloads, importação e rotas da lixeira; OpenAPI exportado
- [x] **Fase 4 — Front-end** (WEB-05 a 10, 18, 19)
  - [x] 4.1 Scaffold Vite + TS, cliente gerado do OpenAPI, job `web` no CI
  - [x] 4.2 Login e layout
  - [x] 4.3 Mês: lista, formulário, salário e meta, painel do mês
  - [x] 4.4 Ano: gráficos e resumo; downloads e importação
  - [x] 4.4b Lixeira: listar, restaurar, excluir definitivamente, esvaziar (WEB-19)
  - [x] 4.5 Testes Playwright dos fluxos principais
- [ ] **Fase 5 — Execução e entrega** (WEB-14, WEB-15)
  - [ ] 5.1 `controlegastos web` (local)
  - [ ] 5.2 Dockerfile em dois estágios e documentação de hospedagem
  - [ ] 5.3 Atualizar `AGENTS.md`, README e hooks (`checar.py` com `frontend/`)

Importação de extratos bancários: capacidade futura, depois da fase 5, com tela de revisão antes de gravar.

