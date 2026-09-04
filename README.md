# controleGastos

Ferramenta de linha de comando para **controle de gastos pessoais**, que gera planilhas Excel (.xlsx) organizando **receitas**, **despesas** e **investimentos** por mês e por ano.

## Requisitos

- [uv](https://docs.astral.sh/uv/) (gerencia o Python 3.14 e dependências)

## Como usar

```bash
# Instala dependências
uv sync

# Gera a planilha a partir de um JSON de entrada
uv run controlegastos gerar data/entradas/exemplo.json -o saida/planilha.xlsx

# Com log detalhado
uv run controlegastos gerar data/entradas/exemplo.json -o saida/planilha.xlsx -v
```

## Entrada de dados

Coloque seus lançamentos em JSON em `data/entradas/`. Veja o formato completo em [AGENTS.md](AGENTS.md#entrada-de-dados-json) e um exemplo em `data/entradas/exemplo.json`.

## Saída

Planilha `.xlsx` com:

- **Resumo Geral** — totais de receitas, despesas, investimentos e saldo livre por mês/ano.
- **Aba por mês** (ex.: `2025-01`) — lançamentos de receitas, despesas e investimentos com totais e saldo livre.

Convenção: `saldo_livre = receitas - despesas - investimentos`.

## Documentação para máquinas/agentes

- [AGENTS.md](AGENTS.md) — guia de desenvolvimento para agentes de IA.
- [PROMPTS.md](PROMPTS.md) — histórico de instruções do usuário; leia antes de alterar o projeto.