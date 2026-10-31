# Produto: controleGastos

Resumo para agentes. A fonte de verdade é o [AGENTS.md](../../AGENTS.md); em caso de conflito, ele prevalece e este arquivo deve ser corrigido.

## Propósito

Ferramenta de controle de gastos pessoais, simples e auditável. Os lançamentos ficam em arquivos JSON versionáveis e a planilha é gerada por comando, sempre com os mesmos critérios de totalização.

## Público-alvo

Pessoa que cuida das próprias finanças e prefere manter os dados em arquivos de texto (JSON) ou registrá-los por uma interface web local, sem depender de planilha manual.

## Saídas

- Principal: planilha Excel (.xlsx) com Resumo Geral, uma aba por mês e aba Gráficos.
- Complementos: exportação CSV (lançamentos e resumo mensal) e interface web local para registrar lançamentos e baixar os arquivos.

## Roadmap desta fase (ordem de prioridade)

1. (A) Validação de schema do JSON, com mensagens claras e caminho do erro.
2. (B) Exportação CSV (`--formato xlsx|csv|ambos`).
3. (C) Interface web (`controlegastos ui`, dependência opcional).
4. (E) Gráficos extras: evolução do patrimônio, ranking de categorias de despesa e comparativo entre meses.

## Fora de escopo

- Importação de extratos bancários (OFX, CSV de banco). Fica para uma fase futura.

## Specs

O plano detalhado desta fase está em `.kiro/specs/controlegastos-agentes-ia/` (requirements, design e tasks).
