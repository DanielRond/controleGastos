# AGENTS.md

Guia para agentes de IA (e humanos) trabalhando neste repositório. É a **fonte única de verdade**: o Kiro o carrega automaticamente e não há steering duplicado.

## Propósito

Ferramenta de **controle de gastos pessoais** que gera planilhas Excel (.xlsx) e CSV a partir de arquivos JSON, organizando receitas, despesas e investimentos por mês e por ano. Simples e auditável: dados em texto versionável, mesmos critérios de totalização sempre.

Fora de escopo: importação de extratos bancários e interface web (adiadas, sem prazo).

## Stack

- **Python 3.14** gerenciado via [uv](https://docs.astral.sh/uv/); CLI, sem framework web
- **openpyxl** (planilha e gráficos), **pytest** + **hypothesis** (testes), **ruff** (lint)

## Comandos principais

```bash
uv sync                                                              # instala dependências
uv run controlegastos gerar data/entradas/exemplo.json -o saida/planilha.xlsx
uv run controlegastos gerar data/entradas/exemplo.json -o saida/planilha.xlsx --formato ambos  # xlsx | csv | ambos
uv run controlegastos gerar ... -v                                   # log detalhado
uv run pytest                                                        # testes
uv run ruff check .                                                  # estilo
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
  generator.py       # gera .xlsx: Resumo Geral, abas AAAA-MM e Gráficos (área de apoio nas colunas Q+)
  exportador_csv.py  # CSV de lançamentos e CSV de resumo mensal (UTF-8, vírgula, ponto decimal)
tests/               # pytest: unitários e propriedades (hypothesis); nada de testes que dependam de UI
scripts/checar.py    # ruff + testes do módulo alterado; usado pelo hook de salvar (portável)
docs/media/          # capturas da planilha usadas no README (só dados fictícios)
.kiro/               # agentes, hooks, steering manual e specs (ver abaixo)
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

1. **Documentação é a fonte de verdade**: siga este arquivo. `PROMPTS.md` é local e não versionado.
2. **Commits só quando o usuário pedir ou autorizar** a versionar. Nunca `push` na `main`; nunca versionar dados pessoais (`data/entradas/20*.json`) nem alterações locais que o usuário não pediu.
3. Valores monetários são **Decimal**, nunca float (float só ao gravar células do openpyxl).
4. Ao mudar o esquema, atualize **juntos**: `loader.py`, `validador.py`, `data/entradas/exemplo.json` e este arquivo.
5. Nomes de identificadores seguem o padrão já existente do pacote (português: `LivroCaixa`, `carregar_json`); documentação e mensagens ao usuário em português. Migrar para inglês só se o usuário pedir, em mudança separada.
6. Após mexer em dependências, rode `uv sync` e valide com uma geração de planilha.
7. Toda mudança de código passa por `uv run ruff check .` e `uv run pytest` antes de ser dada como pronta.

## Fluxo com IA (Kiro)

- **Specs** em `.kiro/specs/<feature>/` (requirements, design, tasks): um spec por feature, enxuto; ao concluir, o que for permanente vai para este arquivo e o spec fica como histórico.
- **Agentes** em `.kiro/agents/`: `planejador` (só escreve em `.kiro/specs/`), `implementador` (código e testes; não escreve em `.kiro/` nem `.github/`; não faz commit), `qa` (só escreve em `tests/`), `documentacao` (README, este arquivo, `docs/`).
- **Hooks** em `.kiro/hooks/`: checagens ao salvar (`scripts/checar.py`) e lembrete do esquema.
- **Steering** só manual: `/revisar-documentacao` compara README e este arquivo com o código.
