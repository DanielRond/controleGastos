# AGENTS.md

Guia para agentes de IA (e humanos) trabalhando neste repositório. É a **fonte única de verdade**: o Kiro o carrega como steering, o Claude Code o importa por `CLAUDE.md`, os agentes customizados são instruídos a lê-lo e não há contexto duplicado.

## Propósito

Ferramenta de **controle de gastos pessoais** que gera planilhas Excel (.xlsx) e CSV a partir de arquivos JSON, organizando receitas, despesas e investimentos por mês e por ano. Simples e auditável: dados em texto versionável, mesmos critérios de totalização sempre.

Próximo grande passo: **interface web** (FastAPI + SPA React/TypeScript, SQLite, login; local e hospedada), em fases: a Fase 1 (camada de serviço) está pronta; a próxima é o armazenamento. Ver `specs/interface-web`. Importação de extratos bancários fica para depois da web.

## Stack

- **Python 3.14** gerenciado via [uv](https://docs.astral.sh/uv/); hoje só CLI, sem framework web
- **openpyxl** (planilha e gráficos), **pytest** + **hypothesis** (testes), **ruff** (lint)
- Planejado para a web (ainda não instalado): FastAPI, SQLAlchemy + SQLite, React + TypeScript; ver `specs/interface-web/design.md`

## Comandos principais

```bash
uv sync                                                              # instala dependências
uv run controlegastos gerar data/entradas/exemplo.json -o saida/planilha.xlsx
uv run controlegastos gerar data/entradas/exemplo.json -o saida/planilha.xlsx --formato ambos  # xlsx | csv | ambos
uv run controlegastos gerar ... -v                                   # log detalhado
uv run pytest                                                        # testes
uv run ruff check .                                                  # estilo (use --no-cache ao criar módulos novos)
uv run python scripts/conferir_specs.py                              # todo requisito vigente tem teste
uv run python scripts/sincronizar_agentes.py                         # regenera .claude/agents a partir de .kiro/agents
uv add <pacote>                                                      # nova dependência (use limites >=X,<Y)
```

No Windows (PowerShell) use `;` em vez de `&&`. Hooks e scripts do projeto não dependem de shell.

## Estrutura do projeto

```
data/entradas/       # JSONs. exemplo*.json são fictícios e públicos; 20*.json são pessoais (não versionar)
saida/               # Planilhas e CSV gerados (ignorado pelo git)
src/controlegastos/
  cli.py             # argparse: subcomando `gerar` (-o, --formato, -v)
  modelo.py          # dataclasses Receita, Despesa, Investimento, Mes, Ano, LivroCaixa (totais em Decimal)
  validador.py       # valida o JSON bruto e devolve todos os erros com caminho (só biblioteca padrão)
  loader.py          # lê JSON, valida (ErroDeValidacaoJSON) e constrói LivroCaixa
  generator.py       # gera .xlsx (arquivo ou bytes): Resumo Geral, abas AAAA-MM e Gráficos (área de apoio nas colunas Q+)
  resumo.py          # dados dos gráficos (patrimônio, ranking, variação do saldo) em Decimal, sem openpyxl
  exportador_csv.py  # CSV de lançamentos e CSV de resumo mensal (UTF-8, vírgula, ponto decimal)
  servico.py         # casos de uso (carregar, gerar, exportar; em arquivo ou em memória); a CLI só chama este módulo
tests/               # pytest: unitários e propriedades (hypothesis); cada teste cita o ID do spec (`# Spec: VAL-03`)
specs/               # specs por capacidade (lancamentos, validacao, exportacao, planilha, armazenamento, interface-web); ver specs/README.md
scripts/             # checar.py (hook), conferir_specs.py (spec↔teste), sincronizar_agentes.py (Kiro→Claude)
docs/media/          # capturas da planilha usadas no README (só dados fictícios)
.kiro/               # agentes, hooks e steering manual; .claude/ e CLAUDE.md para o Claude Code
.github/workflows/   # CI: uv sync, ruff, pytest em Python 3.14
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
2. **Versionamento autônomo**: commite conforme necessário, sem pedir licença, em branch de trabalho (`feat/`, `fix/`, `docs/`, `chore/`), com commits pequenos e temáticos (Conventional Commits em português) e a suíte verde. Nunca commite ou dê `push` na `main`, nunca `push --force` nem `--no-verify`, nunca versione dados pessoais (`data/entradas/20*.json`) nem alterações locais que não são suas. Merge de PR é do usuário.
3. Valores monetários são **Decimal**, nunca float (float só ao gravar células do openpyxl).
4. Ao mudar o esquema, atualize **juntos**: `loader.py`, `validador.py`, `data/entradas/exemplo.json`, `specs/validacao/spec.md` e este arquivo.
5. Nomes de identificadores seguem o padrão já existente do pacote (português: `LivroCaixa`, `carregar_json`); documentação e mensagens ao usuário em português. Migrar para inglês só se o usuário pedir, em mudança separada.
6. Após mexer em dependências, rode `uv sync` e valide com uma geração de planilha.
7. Toda mudança de código passa por `uv run ruff check .` e `uv run pytest` (inclui a conferência de specs) antes de ser dada como pronta.
8. **Spec primeiro**: comportamento novo ou alterado entra em `specs/<capacidade>/spec.md` (IDs novos, nunca renumerar) e o usuário aprova antes de codar. Agentes de implementação não editam `spec.md`.

## Fluxo com IA (Kiro e Claude Code)

- **Specs** em `specs/<capacidade>/spec.md`, neutros entre Kiro e Claude Code, em pt-BR com IDs estáveis; permanecem depois de prontos e o código responde a eles (fluxo em `specs/README.md`). `design.md`/`tasks.md` só em mudanças grandes.
- **Agentes**: a fonte é `.kiro/agents/`; `.claude/agents/` é gerado por `uv run python scripts/sincronizar_agentes.py` (um teste falha se defasado). Papéis: `planejador` (só `specs/`), `implementador` (código e testes; não escreve em `.kiro/`, `.github/`, `AGENTS.md` nem `spec.md`; pode commitar, não faz push), `qa` (só `tests/`; pode commitar, não faz push), `documentacao` (README, este arquivo, `docs/`). No Kiro as restrições são impostas por `permissions.rules`; no Claude Code valem como instrução.
- **Hooks**: `scripts/checar.py` roda ruff e os testes do módulo editado (Kiro: `.kiro/hooks/checar-ao-salvar.json`; Claude Code: `.claude/settings.json`). O lembrete de esquema (`lembrete-esquema.json`) existe só no Kiro; no Claude Code vale a regra 4. No Kiro o hook de salvar só dispara quando o **agente** edita um arquivo, não quando você salva no editor.
- **Steering** só manual: `/revisar-documentacao` compara README e este arquivo com o código.
