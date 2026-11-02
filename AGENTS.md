# AGENTS.md

Guia para agentes de IA (e humanos) trabalhando neste repositório. É a **fonte única de verdade**: o Kiro o carrega como steering, o Claude Code o importa por `CLAUDE.md`, os agentes customizados são instruídos a lê-lo e não há contexto duplicado.

## Propósito

Ferramenta de **controle de gastos pessoais**: registra receitas, despesas e investimentos por mês e ano e gera planilha Excel, CSV e painéis. Dois jeitos de usar: **interface web** com login (SQLite; local ou hospedada em Docker) e **CLI** que gera a planilha a partir de JSON. Simples e auditável: mesmos critérios de totalização sempre; o JSON é formato de entrada, saída e backup. Pronto: validação, CSV, gráficos, serviço, armazenamento, API, front-end e hospedagem. Próximo: importação de extratos bancários (ver `specs/interface-web/tasks.md`).

## Stack

- **Python 3.14** com [uv](https://docs.astral.sh/uv/); `uv sync --extra web` instala a web (FastAPI, SQLAlchemy, Alembic, Argon2)
- **openpyxl** (planilha), **pytest** + **hypothesis** (testes), **ruff** (lint)
- Front-end em `frontend/`: React + TypeScript + Vite, Vitest, Playwright; **Node 24+** (`.nvmrc`)

## Comandos principais

```bash
uv sync --extra web                                       # instala tudo do Python
uv run controlegastos gerar data/entradas/exemplo.json -o saida/planilha.xlsx [--formato xlsx|csv|ambos] [-v]
uv run controlegastos banco atualizar                     # cria/atualiza o SQLite (DATABASE_URL ou dados/)
uv run controlegastos usuario criar NOME [--senha-stdin]  # conta de acesso à web
uv run controlegastos web                                 # interface em http://127.0.0.1:8000 (precisa do front compilado)
uv run pytest && uv run ruff check . --no-cache           # testes (inclui conferência de specs) e estilo
uv run python scripts/conferir_specs.py                   # todo requisito vigente tem teste
uv run python scripts/exportar_openapi.py                 # atualiza specs/api/openapi.json (um teste exige em dia)
uv run python scripts/sincronizar_agentes.py              # regenera .claude/agents a partir de .kiro/agents
(cd frontend && npm ci && npm run api && npm test && npm run build)   # front; `npm run api` após mudar o OpenAPI
(cd frontend && npx playwright install chromium && npm run e2e)       # ponta a ponta (precisa do build)
uv add <pacote>                                           # nova dependência (limites >=X,<Y)
```

No Windows (PowerShell) use `;` em vez de `&&`. Hooks e scripts não dependem de shell.

## Estrutura do projeto

```
src/controlegastos/
  cli.py             # argparse: gerar, banco, usuario, web
  modelo.py          # dataclasses Receita, Despesa, Investimento, Mes, Ano, LivroCaixa (Decimal)
  validador.py       # valida o JSON bruto, devolve todos os erros com caminho (só stdlib)
  loader.py          # JSON -> valida -> LivroCaixa
  generator.py       # .xlsx (arquivo ou bytes): Resumo Geral, abas AAAA-MM, Gráficos
  resumo.py          # dados dos gráficos e percentuais, em Decimal, sem openpyxl
  exportador_csv.py  # CSV de lançamentos e de resumo mensal
  servico.py         # casos de uso (carregar, gerar, exportar); a CLI só chama este módulo
  armazenamento/     # SQLAlchemy + Alembic: repositório por usuário, centavos, lixeira
  web/               # FastAPI: segurança (Argon2, sessão, CSRF), esquemas, rotas /api, serve o front
frontend/            # SPA (cliente da API gerado em src/api/schema.d.ts); e2e/ com Playwright
specs/               # specs por capacidade (ver specs/README.md); api/openapi.json é o contrato
tests/               # pytest; cada teste cita o ID do spec (`# Spec: VAL-03`)
scripts/             # hook (checar), conferir_specs, sincronizar_agentes, exportar_openapi, servidor_e2e, testar_imagem
data/entradas/       # JSONs: exemplo*.json são públicos e fictícios; 20*.json são pessoais (não versionar)
dados/ saida/        # banco SQLite local e arquivos gerados (dados pessoais; ignorados pelo git)
docs/                # media/ (capturas fictícias) e hospedagem.md; Dockerfile e docker-compose.yml na raiz
.kiro/ .claude/      # agentes, hooks e steering; CLAUDE.md importa este arquivo
.github/workflows/   # CI: ci (ruff, pytest), web (front), e2e (Playwright), imagem (Docker)
```

## Entrada de dados (JSON)

```json
{
  "moeda": "BRL",
  "anos": [
    {
      "ano": 2025,
      "meses": [
        {
          "mes": 1,
          "salario": 5000.00,
          "meta_investimento": 1000.00,
          "receitas":    [{"descricao": "...", "valor": 0.0, "dia": 1, "categoria": "..."}],
          "despesas":    [{"descricao": "...", "valor": 0.0, "dia": 1, "categoria": "..."}],
          "investimentos":[{"tipo": "...", "ativo": "...", "descricao": "...", "valor": 0.0, "dia": 1, "categoria": "..."}]
        }
      ]
    }
  ]
}
```

- Opcionais: `salario`, `receitas`, `despesas`, `investimentos`, `meta_investimento`, `categoria` (padrão `geral`), `ativo`.
- Obrigatórios por lançamento: `descricao`, `valor` (número finito, não booleano), `dia` (válido para o mês/ano); em investimentos, também `tipo`.
- O validador reporta **todos** os erros de uma vez, com o caminho (ex.: `anos[0].meses[2].despesas[1].valor`); a CLI imprime cada um e retorna 1 sem gerar arquivos.
- `tipo` de investimento: `renda_fixa`, `fii`, `cripto`. `ativo` é o ticker/nome (ex.: `KNSC11`, `BTC`, `CDI`) e aparece na coluna Categoria da aba do mês. Taxas/liquidação entram como investimento com `descricao` própria e o mesmo `tipo`.
- `meta_investimento` é o valor pretendido para o mês; a planilha compara com o total investido.

## Saída

- **Resumo Geral**: totais por mês/ano de receitas, despesas, investimentos e saldo livre.
- **Aba por mês** (`2025-01`): Receitas, Despesas, Investimentos (ativo, % do total, subtotal e % por classe, comparação com a meta).
- **Gráficos**: pizza por classe de investimento, barras mensais, evolução do patrimônio (aportes acumulados), ranking de categorias de despesa (`Sem categoria` para vazias/`geral`) e variação do saldo livre entre meses. Gráficos sem dados suficientes são omitidos, sem erro.
- **CSV** (`--formato csv|ambos`): `<nome>-lancamentos.csv` e `<nome>-resumo-mensal.csv`.
- Convenção: `saldo_livre = receitas - despesas - investimentos`.

## Regras para agentes de IA

1. **Documentação é a fonte de verdade**: siga este arquivo.
2. **Versionamento autônomo**: commite conforme necessário, sem pedir licença, em branch de trabalho (`feat/`, `fix/`, `docs/`, `chore/`), com commits pequenos e temáticos (Conventional Commits em português) e a suíte verde. Nunca commite ou dê `push` na `main`, nunca `push --force` nem `--no-verify`, nunca versione dados pessoais (`data/entradas/20*.json`) nem alterações locais que não são suas. **Merge**: o agente abre o PR e o mescla (merge commit, apagando a branch) assim que o CI estiver verde, sem esperar revisão do usuário; nunca mescla com CI vermelho. **Instalações** de ferramentas e dependências necessárias ao projeto (Node via fnm, Playwright, pacotes) são autorizadas.
3. Valores monetários são **Decimal**, nunca float (float só ao gravar células do openpyxl); no banco, centavos inteiros. No JSON, no máximo 2 casas decimais (VAL-13).
4. Ao mudar o esquema, atualize **juntos**: `loader.py`, `validador.py`, `data/entradas/exemplo.json`, `specs/validacao/spec.md` e este arquivo.
5. Nomes de identificadores seguem o padrão já existente do pacote (português: `LivroCaixa`, `carregar_json`); documentação e mensagens ao usuário em português. Migrar para inglês só se o usuário pedir, em mudança separada.
6. Após mexer em dependências, rode `uv sync` e valide com uma geração de planilha.
7. Toda mudança de código passa por `uv run ruff check .` e `uv run pytest` (inclui a conferência de specs) antes de ser dada como pronta.
8. **Spec primeiro**: comportamento novo ou alterado entra em `specs/<capacidade>/spec.md` (IDs novos, nunca renumerar), em commit próprio antes do código. Não precisa de aprovação do usuário quando decorre das decisões já registradas nos specs; se contrariar uma decisão registrada ou criar escopo novo, pergunte. Subagentes de implementação não editam `spec.md`.
9. **Retomada**: o progresso fica em `specs/interface-web/tasks.md` (checkboxes e a seção "Retomada"). Commite e dê push a cada passo concluído e atualize essa seção (branch, último passo, próximo passo), para qualquer agente ou provedor continuar de onde parou.

## Fluxo com IA (Kiro e Claude Code)

- **Specs** em `specs/<capacidade>/spec.md`, neutros entre Kiro e Claude Code, em pt-BR com IDs estáveis; permanecem depois de prontos e o código responde a eles (fluxo em `specs/README.md`). `design.md`/`tasks.md` só em mudanças grandes.
- **Agentes**: a fonte é `.kiro/agents/`; `.claude/agents/` é gerado por `uv run python scripts/sincronizar_agentes.py` (um teste falha se defasado). Papéis: `planejador` (só `specs/`), `implementador` (código e testes; não escreve em `.kiro/`, `.github/`, `AGENTS.md` nem `spec.md`; pode commitar, não faz push), `qa` (só `tests/`; pode commitar, não faz push), `documentacao` (README, este arquivo, `docs/`). No Kiro as restrições são impostas por `permissions.rules`; no Claude Code valem como instrução.
- **Hooks**: `scripts/checar.py` roda ruff e os testes do módulo editado (Kiro: `.kiro/hooks/checar-ao-salvar.json`; Claude Code: `.claude/settings.json`); em `frontend/` roda lint, tipos e testes relacionados. O lembrete de esquema (`lembrete-esquema.json`) existe só no Kiro; no Claude Code vale a regra 4. No Kiro o hook de salvar só dispara quando o **agente** edita um arquivo, não quando você salva no editor.
- **Steering** só manual: `/revisar-documentacao` compara README e este arquivo com o código.
