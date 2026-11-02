---
capacidade: exportacao
codigo: EXP
status: vigente
---

# Capacidade: exportação (formato e CSV)

## Objetivo

Permitir levar os dados para outras ferramentas em CSV, além da planilha `.xlsx`, com os mesmos totais.

## Comportamento

- **EXP-01** `gerar` aceita `--formato xlsx|csv|ambos`; sem a opção, gera só o `.xlsx`.
- **EXP-02** `--formato` inválido exibe mensagem em português (`Valor inválido para --formato. Use: xlsx, csv, ambos.`) e sai com código diferente de 0.
- **EXP-03** CSV de lançamentos, cabeçalho exato `data,tipo,descricao,categoria,ativo,valor`: `data` em `AAAA-MM-DD`; `tipo` é `receita`, `despesa` ou `investimento`; `ativo` só em investimentos; a coluna `categoria` nunca recebe o `tipo` do investimento. Ordem: ano, mês, receitas, despesas, investimentos, mantendo a ordem de inserção.
- **EXP-04** CSV de resumo mensal, cabeçalho exato `ano,mes,receitas,despesas,investimentos,saldo_livre`, uma linha por mês em ordem cronológica.
- **EXP-05** Valores monetários saem de `Decimal`, com duas casas, ponto decimal, sem separador de milhar, arredondamento half-up, ex.: `1200.00`. A quantização acontece só na formatação.
- **EXP-06** Arquivos em UTF-8 sem BOM, delimitador vírgula, fim de linha `\n`; o diretório de destino é criado se não existir.
- **EXP-07** Os nomes derivam de `-o` sem extensão: `saida/planilha.xlsx` gera `saida/planilha-lancamentos.csv` e `saida/planilha-resumo-mensal.csv`.
- **EXP-08** O `saldo_livre` do CSV de resumo é igual ao do Resumo Geral do `.xlsx` para o mesmo mês (comparados a duas casas).
- **EXP-09** A CLI imprime uma linha por arquivo gerado: `Planilha disponível em: ...` (apenas xlsx) ou `Arquivo disponível em: ...` (csv/ambos).
- **EXP-10** Falha de escrita (permissão, arquivo aberto no Excel) gera mensagem em português e código 1, sem reportar sucesso.
- **EXP-11** Round trip: ler o CSV de lançamentos reproduz tipos, datas, textos (inclusive vírgulas, aspas e quebras de linha) e valores do livro.
- **EXP-12** CSV em memória: `exportar_csv_bytes(livros)` devolve os dois CSV (lançamentos e resumo) como bytes UTF-8, idênticos byte a byte aos arquivos que `exportar_csv` grava para o mesmo livro.

## Valores de referência

Para `exemplo.json`, 2025-01: `2025,1,5250.00,1780.00,1000.00,2470.00`.

## Fora de escopo

- Importar CSV de volta como entrada.
- Delimitador `;` e vírgula decimal para Excel pt-BR: o Excel deve importar com delimitador vírgula explícito (documentado no README).

## Perguntas abertas

Nenhuma pendente.

## Rastreabilidade

`exportador_csv.py`, `cli.py`; testes `test_exportador_csv*.py`, `test_cli.py`.
