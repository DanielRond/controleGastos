# Estrutura do projeto

O esquema completo do JSON de entrada está no [AGENTS.md](../../AGENTS.md#entrada-de-dados-json). Não copie o esquema para cá.

## Módulos (`src/controlegastos/`)

| Módulo | Responsabilidade |
|---|---|
| `__init__.py` | Entry point (`main`) do script `controlegastos` |
| `cli.py` | CLI com argparse: subcomandos `gerar` (com `--formato`) e `ui` |
| `modelo.py` | Dataclasses `Receita`, `Despesa`, `Investimento`, `Mes`, `Ano`, `LivroCaixa`, com totais em Decimal |
| `validador.py` | Valida o JSON bruto e devolve todos os erros com o caminho (ex.: `anos[0].meses[2].despesas[1].valor`). Só biblioteca padrão |
| `loader.py` | Lê o JSON, chama o validador e constrói o `LivroCaixa` |
| `generator.py` | Gera o .xlsx: Resumo Geral, abas `AAAA-MM` e aba Gráficos, alimentada por uma área de apoio |
| `exportador_csv.py` | Gera o CSV de lançamentos e o CSV de resumo mensal |
| `servico.py` | Servico_Core: carregar, validar, salvar, gerar e exportar. Não importa o framework de UI |
| `interface_web.py` | Interface Streamlit. Único módulo que importa `streamlit` |

## Diretórios

| Diretório | Papel |
|---|---|
| `tests/` | Suíte pytest (unitários e propriedades com hypothesis). Nenhum teste inicia a UI |
| `data/entradas/` | JSONs de entrada. `exemplo.json` e `exemplo-completo.json` são fictícios e públicos; `20*.json` são dados pessoais e não são versionados |
| `docs/media/` | Capturas da planilha usadas no README (só dados fictícios) |
| `saida/` | Arquivos gerados (.xlsx e .csv). Criado automaticamente e ignorado pelo git |
| `.kiro/` | Steering, agentes, hooks e specs para desenvolvimento com IA |
