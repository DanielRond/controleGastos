# AGENTS.md

Guia para agentes de IA (e humanos) trabalhando neste repositório.

## Propósito

Ferramenta de **controle de gastos pessoais** que gera planilhas Excel (.xlsx) a partir de arquivos JSON, organizando receitas, despesas e investimentos por mês e por ano.

## Stack

- **Python 3.14** gerenciado via [uv](https://docs.astral.sh/uv/)
- Geração de planilhas: **openpyxl**
- Sem framework web; ferramenta de linha de comando

## Comandos principais

```bash
# Instalar dependências e sincronizar o ambiente
uv sync

# Gerar planilha a partir de um JSON de entrada
uv run controlegastos gerar data/entradas/exemplo.json -o saida/planilha.xlsx

# Com log detalhado
uv run controlegastos gerar data/entradas/exemplo.json -o saida/planilha.xlsx -v

# Adicionar nova dependência
uv add <pacote>

# Rodar os testes automatizados
uv run pytest

# Rodar checagens de estilo
uv run ruff check .
```

## Estrutura do projeto

```
data/
  entradas/          # JSONs com lançamentos (fonte de dados)
saida/               # Planilhas geradas (criada automaticamente)
src/controlegastos/
  __init__.py        # entry point (main)
  cli.py             # argparse CLI
  modelo.py          # dataclasses: Receita, Despesa, Investimento, Mes, Ano, LivroCaixa
  loader.py          # lê JSON e constrói LivroCaixa
  generator.py       # gera .xlsx com openpyxl (Resumo Geral + aba por mês)
pyproject.toml       # metadados e script `controlegastos`
PROMPTS.md           # histórico de prompts/instruções do usuário
AGENTS.md            # este arquivo
```

## Entrada de dados (JSON)

Todo JSON em `data/entradas/` segue o esquema:

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

Campos opcionais: `salario`, `receitas`, `despesas`, `investimentos`, `meta_investimento`.

Em investimentos:
- `tipo` indica a classe do ativo. Valores conhecidos: `renda_fixa`, `fii` (fundos imobiliários), `cripto` (criptomoedas).
- `ativo` é o ticker/nome do ativo (opcional), ex.: `KNSC11`, `BTC`, `CDI`. Quando presente, é exibido na coluna Categoria da aba do mês.
- Taxas/liquidação podem ser lançadas como item de investimento com `descricao` própria e o mesmo `tipo`.
- `meta_investimento` é o valor que se pretende investir no mês (ex.: 250.00); a planilha compara com o total investido.

## Saída (planilha)

- **Resumo Geral**: totais por mês/ano de receitas, despesas, investimentos e saldo livre.
- **Aba por mês** (`2025-01`): seções Receitas, Despesas, Investimentos.
  - Em investimentos: cada lançamento mostra o ativo e o % do total investido na coluna extra; subtotal e % por tipo/classe; e comparação com `meta_investimento`.
- Convenção: `saldo_livre = receitas - despesas - investimentos`.

## Regras para agentes de IA

1. **Sempre leia PROMPTS.md** antes de alterar o repositório — ele registra o histórico de instruções do usuário.
2. **Nunca commite sem pedido explícito** do usuário.
3. Valores monetários devem ser **Decimal**, nunca float. Evitar pontos flutuantes.
4. Ao mudar o esquema de dados, atualize **loader.py**, **exemplo.json** e **AGENTS.md** juntos.
5. Código em inglês para nomes/identificadores; documentação e mensagens ao usuário em português.
6. Rodar `uv sync` após mexer nas dependências e validar com uma geração de planilha.