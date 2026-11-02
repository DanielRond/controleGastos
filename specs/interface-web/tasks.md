# Plano: interface web

## Retomada (para qualquer agente ou provedor)

Atualize esta seção a cada passo concluído, junto do commit.

- **Estado**: Fase 2 em andamento (STO-* e VAL-13 vigentes, ainda sem testes: nesta branch o conferidor de specs falha até eles existirem; o PR só é mesclado verde).
- **Branch atual**: `feat/fase2-armazenamento`.
- **Último passo concluído**: 2.1 (stack instalada e verificada em Python 3.14; extra `web` no `pyproject.toml` e no CI) e commit de spec.
- **Próximo passo**: testes primeiro (centavos, repositório, lixeira, importação, migração), depois `armazenamento/` e VAL-13.
- **Como retomar**: `git checkout main && git pull`; ler `AGENTS.md`, este arquivo, `design.md` e os specs; criar a branch da tarefa; spec primeiro, testes antes do código, `uv run ruff check . --no-cache`, `uv run pytest` e `uv run python scripts/conferir_specs.py` verdes antes de cada commit; abrir PR e mesclar com o CI verde.
- **Ambiente**: Python 3.14 via uv; Docker disponível; Node 18 no sistema (a Fase 4 exige Node 20+, instalar com fnm).

Cada fase é um PR pequeno, com spec primeiro, testes antes do código e revisão humana. Os status `rascunho` passam a `vigente` quando a fase correspondente começar (aí o CI exige um teste por requisito).

- [x] **Fase 0 — Decisões**: perguntas abertas respondidas e specs aprovados pelo usuário.
- [x] **Fase 1 — Serviço (sem mudar comportamento)** (LAN-07, PLN-12, PLN-13, EXP-12)
  - [x] 1.1 Extrair `servico.py` e `resumo.py` (dados dos gráficos públicos); CLI chama o serviço
  - [x] 1.2 Geração do `.xlsx` e dos CSV em memória (bytes)
  - Critério cumprido: suíte existente verde; saída idêntica à anterior (CSV byte a byte, `.xlsx` célula a célula).
- [ ] **Fase 2 — Armazenamento** (STO-01 a STO-14, VAL-13)
  - [x] 2.1 Extra `web` com instalação real da stack em Python 3.14; `armazenamento` vigente
  - [ ] 2.2 Repositório por usuário, carga para `LivroCaixa`, isolamento (STO-06)
  - [ ] 2.3 Importar/exportar JSON transacional (recusa mês existente; `substituir` explícito), valor com no máximo 2 casas (STO-11) e `controlegastos banco atualizar`
  - [ ] 2.4 Exclusão lógica e lixeira no repositório (STO-12, STO-13), com os testes de propriedade do design
- [ ] **Fase 3 — API e autenticação** (WEB-01 a 08, 11, 12, 13, 16, 17, 19)
  - [ ] 3.1 App FastAPI, sessão, login, CSRF, limite de tentativas, `controlegastos usuario criar`
  - [ ] 3.2 Rotas de meses e lançamentos com erros `{caminho, mensagem}`
  - [ ] 3.3 Resumo anual, downloads, importação e rotas da lixeira; OpenAPI exportado
- [ ] **Fase 4 — Front-end** (WEB-05 a 10, 18, 19)
  - [ ] 4.1 Scaffold Vite + TS, cliente gerado do OpenAPI, job `web` no CI
  - [ ] 4.2 Login e layout
  - [ ] 4.3 Mês: lista, formulário, salário e meta, painel do mês
  - [ ] 4.4 Ano: gráficos e resumo; downloads e importação
  - [ ] 4.4b Lixeira: listar, restaurar, excluir definitivamente, esvaziar (WEB-19)
  - [ ] 4.5 Testes Playwright dos fluxos principais
- [ ] **Fase 5 — Execução e entrega** (WEB-14, WEB-15)
  - [ ] 5.1 `controlegastos web` (local)
  - [ ] 5.2 Dockerfile em dois estágios e documentação de hospedagem
  - [ ] 5.3 Atualizar `AGENTS.md`, README e hooks (`checar.py` com `frontend/`)

Importação de extratos bancários: capacidade futura, depois da fase 5, com tela de revisão antes de gravar.

