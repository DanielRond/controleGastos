---
capacidade: planilha
codigo: PLN
status: vigente
---

# Capacidade: planilha Excel

## Objetivo

Gerar um `.xlsx` legível para acompanhar o mês e a evolução: resumo geral, uma aba por mês e gráficos.

## Comportamento

- **PLN-01** A planilha tem a aba `Resumo Geral`, uma aba `AAAA-MM` por mês (em ordem cronológica) e, havendo ao menos um mês, a aba `Gráficos`. O diretório de destino é criado se não existir.
- **PLN-02** `Resumo Geral` mostra, por mês e por ano, receitas, despesas, investimentos e saldo livre, com o cabeçalho `Ano`, `Mês`, `Receitas`, `Despesas`, `Investimentos`, `Saldo Livre`.
- **PLN-03** A aba do mês tem as seções Receitas, Despesas e Investimentos, os totais de cada uma e a linha `Saldo Livre`.
- **PLN-04** Em investimentos: ativo na coluna Categoria, % de cada lançamento sobre o total investido, subtotal e % por classe (renda fixa, FIIs, cripto) e comparação com a meta (`Meta de Investimento` e `Falta investir`).
- **PLN-05** A aba `Gráficos` tem a pizza de investimentos por classe (se houver investimentos) e as barras mensais de receitas, despesas, investimentos e saldo livre.
- **PLN-06** Evolução do patrimônio: linha dos aportes acumulados, só com 2 meses ou mais e total investido maior que zero.
- **PLN-07** Ranking de categorias de despesa: barras em ordem decrescente de total, no máximo 10 categorias. Categoria vazia, só espaços ou `geral` entra como `Sem categoria`. A soma de todo o ranking é o total de despesas.
- **PLN-08** Comparativo entre meses: variação do saldo livre em relação ao mês anterior, com 2 meses ou mais.
- **PLN-09** Dados insuficientes omitem apenas o gráfico afetado; gerar a planilha nunca falha por isso, inclusive com livro vazio.
- **PLN-10** Eixos visíveis nos gráficos com eixos; no comparativo, os rótulos dos meses ficam abaixo das barras negativas.
- **PLN-11** Gráficos são alimentados por uma área de apoio na própria aba `Gráficos` (colunas `Q` em diante), sem dependências além do openpyxl.
- **PLN-12** Planilha em memória: `gerar_planilha_bytes(livros)` devolve os bytes de um `.xlsx` válido com as mesmas abas, células (valores e formatos) e gráficos que `gerar_planilha` grava em arquivo para o mesmo livro, sem escrever em disco.
- **PLN-13** Os dados dos gráficos são públicos e independentes do openpyxl, em `resumo.py`: `patrimonio_acumulado`, `ranking_despesas` e `variacao_saldo`, todos em `Decimal`. São os mesmos dados que alimentam a planilha e valem as regras de PLN-06 a PLN-08.

## Valores de referência

Para `exemplo-completo.json`: a aba `Gráficos` tem 5 gráficos (pizza, barras mensais, patrimônio, ranking, comparativo). Para um único mês com despesa e investimento: pizza, barras mensais e ranking.

## Fora de escopo

- Formatação condicional, fórmulas do Excel (os valores são gravados calculados).
- Rendimentos de investimentos no gráfico de patrimônio.

## Perguntas abertas

Nenhuma pendente.

## Rastreabilidade

`generator.py`, `resumo.py`; testes `test_generator*.py`. Capturas em `docs/media/`.
