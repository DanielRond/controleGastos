---
capacidade: lancamentos
codigo: LAN
status: vigente
---

# Capacidade: lançamentos

## Objetivo

Transformar o JSON de entrada em um livro-caixa em memória (`LivroCaixa`) com totais corretos e auditáveis, sempre com os mesmos critérios.

## Comportamento

- **LAN-01** Um JSON válido vira um `LivroCaixa` organizado em anos, meses e lançamentos (receitas, despesas, investimentos). O `salario` do mês vira uma receita "Salário", categoria `salario`, no dia 1.
- **LAN-02** Todo valor monetário do modelo é `Decimal`, convertido de `str(valor)` do JSON; nunca `float`. A conversão para `float` só ocorre ao gravar células do openpyxl.
- **LAN-03** Totais do mês: `total_receitas`, `total_despesas`, `total_investimentos` e `saldo_livre = receitas - despesas - investimentos`. Totais do ano somam os meses.
- **LAN-04** `dia` define a data do lançamento (`date(ano, mes, dia)`). `categoria` ausente vale `geral`.
- **LAN-05** `meta_investimento` e `salario` são opcionais; mês sem eles carrega sem erro, com meta ausente.
- **LAN-06** Ano e mês ausentes no livro são criados sob demanda (`ano()`/`mes()`), sem sobrescrever os existentes.
- **LAN-07** `servico.py` concentra as operações de aplicação: carregar de arquivo ou de dicionário (validando), gerar planilha e CSV em arquivo ou em memória, e gerar os arquivos conforme o formato (`xlsx`, `csv`, `ambos`). A CLI usa apenas esse serviço; mensagens, códigos de saída e arquivos continuam idênticos (VAL-11, EXP-01, EXP-09, EXP-10).

## Valores de referência (`data/entradas/exemplo.json`)

| Mês | Receitas | Despesas | Investimentos | Saldo livre | Meta |
|---|---|---|---|---|---|
| 2025-01 | 5250.00 | 1780.00 | 1000.00 | 2470.00 | 1000.00 |
| 2025-02 | 5000.00 | 1400.00 | 1000.00 | 2600.00 | |

## Fora de escopo

- Moedas diferentes de BRL e conversão cambial (`moeda` é apenas informativo).
- Rendimentos de investimentos (só aportes).

## Perguntas abertas

- Quando houver interface web: os lançamentos continuam em JSON versionável ou passam a ter outro armazenamento? (ver `interface-web`)

## Rastreabilidade

`modelo.py`, `loader.py`, `servico.py`; testes `test_modelo.py`, `test_loader.py`.
