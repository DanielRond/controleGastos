# Plano: interface web

## Retomada (para qualquer agente ou provedor)

Atualize esta seção a cada passo concluído, junto do commit.

- **Estado**: Fases 1 a 3, 4a e 4b mescladas. Fase 4c (ano, lixeira, arquivos) pronta na branch `feat/fase4c-ano-lixeira-arquivos`, a mesclar. Falta 4d: Playwright e promoção do spec `frontend` a `vigente`.
- **Branch atual**: `feat/fase4c-ano-lixeira-arquivos`.
- **Último passo concluído**: 4c (WEB-24, 25, 26; 74 testes Vitest). Gráficos ECharts carregados sob demanda, só desenhados com canvas; cada gráfico tem tabela de dados como alternativa em texto. Lixeira com confirmação em linha (`alertdialog`, foco em Cancelar). Arquivos: downloads por link, importação com erros por caminho e conflito 409 com "substituir".
- **Próximo passo**: 4d. (1) Servir o front compilado pela API (`src/controlegastos/web/static`, fallback para `index.html` fora de `/api`), pois o Playwright precisa de um app real: um `scripts/servidor_e2e.py` sobe `criar_app` com SQLite temporário e um usuário, via uvicorn. (2) Instalar Playwright no `frontend/` (navegador Chromium, ~150 MB) e escrever `e2e/*.spec.ts` citando `// Spec: WEB-xx` (login, lançar e ver totais, editar/apagar/restaurar, ano com gráficos desenhados, importar com conflito, acessibilidade por teclado). (3) Job de CI para o E2E. (4) Passar `specs/frontend` a `vigente` (todo ID precisa de teste; WEB-18 e 27 já têm). Depois, Fase 5 (`controlegastos web`, Dockerfile).
- **Node**: `export PATH=$HOME/.local/share/node/node-v24.22.2-linux-x64/bin:$PATH` (o do sistema é o 18).
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
- [ ] **Fase 4 — Front-end** (WEB-05 a 10, 18, 19)
  - [x] 4.1 Scaffold Vite + TS, cliente gerado do OpenAPI, job `web` no CI
  - [x] 4.2 Login e layout
  - [x] 4.3 Mês: lista, formulário, salário e meta, painel do mês
  - [x] 4.4 Ano: gráficos e resumo; downloads e importação
  - [x] 4.4b Lixeira: listar, restaurar, excluir definitivamente, esvaziar (WEB-19)
  - [ ] 4.5 Testes Playwright dos fluxos principais
- [ ] **Fase 5 — Execução e entrega** (WEB-14, WEB-15)
  - [ ] 5.1 `controlegastos web` (local)
  - [ ] 5.2 Dockerfile em dois estágios e documentação de hospedagem
  - [ ] 5.3 Atualizar `AGENTS.md`, README e hooks (`checar.py` com `frontend/`)

Importação de extratos bancários: capacidade futura, depois da fase 5, com tela de revisão antes de gravar.

