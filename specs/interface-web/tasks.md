# Plano: interface web

Cada fase é um PR pequeno, com testes antes e revisão humana. Começa depois da aprovação de `spec.md`, `design.md` e `../armazenamento/spec.md` e do merge do PR #1. Os status `rascunho` passam a `vigente` quando a fase correspondente começar (aí o CI exige os testes).

- [ ] **Fase 0 — Aprovação**: responder as perguntas abertas, aprovar os specs; promover `armazenamento` e `interface-web` a `vigente` fase a fase.
- [ ] **Fase 1 — Serviço (sem mudar comportamento)**
  - [ ] 1.1 Extrair `servico.py` e `resumo.py` (dados dos gráficos públicos); CLI chama o serviço
  - [ ] 1.2 Geração do `.xlsx` e dos CSV em memória (bytes)
  - Critério: suíte existente verde; PLN-*, EXP-* inalterados.
- [ ] **Fase 2 — Armazenamento** (STO-01 a STO-10)
  - [ ] 2.1 Extra `web`, modelos SQLAlchemy, centavos, migração inicial
  - [ ] 2.2 Repositório por usuário, carga para `LivroCaixa`, isolamento (STO-06)
  - [ ] 2.3 Importar/exportar JSON transacional e `controlegastos banco atualizar`
  - [ ] 2.4 Resolver a pergunta aberta sobre exclusão (lançamentos) antes de codar o CRUD (fase 3)
- [ ] **Fase 3 — API e autenticação** (WEB-01 a 08, 11, 12, 13, 16, 17)
  - [ ] 3.1 App FastAPI, sessão, login, CSRF, limite de tentativas, `controlegastos usuario criar`
  - [ ] 3.2 Rotas de meses e lançamentos com erros `{caminho, mensagem}`
  - [ ] 3.3 Resumo anual, downloads e importação; OpenAPI exportado
  - [ ] 3.4 Instalação real da stack em Python 3.14 (confirmar o que o dry-run indicou)
- [ ] **Fase 4 — Front-end** (WEB-05 a 10, 18)
  - [ ] 4.1 Scaffold Vite + TS, cliente gerado do OpenAPI, job `web` no CI
  - [ ] 4.2 Login e layout
  - [ ] 4.3 Mês: lista, formulário, salário e meta, painel do mês
  - [ ] 4.4 Ano: gráficos e resumo; downloads e importação
  - [ ] 4.5 Testes Playwright dos fluxos principais
- [ ] **Fase 5 — Execução e entrega** (WEB-14, WEB-15)
  - [ ] 5.1 `controlegastos web` (local)
  - [ ] 5.2 Dockerfile em dois estágios e documentação de hospedagem
  - [ ] 5.3 Atualizar `AGENTS.md`, README e hooks (`checar.py` com `frontend/`)

Importação de extratos bancários: capacidade futura, depois da fase 5.
