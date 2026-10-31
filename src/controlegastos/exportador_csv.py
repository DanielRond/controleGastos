"""Exportação dos lançamentos e do resumo mensal para arquivos CSV.

Gera dois arquivos em UTF-8 (sem BOM), com vírgula como delimitador e ponto
como separador decimal:
- CSV de lançamentos: data, tipo, descricao, categoria, ativo, valor
- CSV de resumo mensal: ano, mes, receitas, despesas, investimentos, saldo_livre

Valores monetários são sempre Decimal; a quantização para duas casas ocorre
apenas na formatação.
"""

from __future__ import annotations

import csv
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

from .modelo import LivroCaixa

CABECALHO_LANCAMENTOS = ["data", "tipo", "descricao", "categoria", "ativo", "valor"]
CABECALHO_RESUMO = ["ano", "mes", "receitas", "despesas", "investimentos", "saldo_livre"]

_DUAS_CASAS = Decimal("0.01")


def caminhos_csv(destino_base: str | Path) -> tuple[Path, Path]:
    """Deriva os caminhos do CSV de lançamentos e do CSV de resumo mensal a partir de -o."""
    destino = Path(destino_base)
    return (
        destino.with_name(f"{destino.stem}-lancamentos.csv"),
        destino.with_name(f"{destino.stem}-resumo-mensal.csv"),
    )


def formatar_decimal(valor: Decimal) -> str:
    """Quantiza para duas casas (ROUND_HALF_UP) e formata com ponto, ex.: '1234.50'."""
    return format(valor.quantize(_DUAS_CASAS, rounding=ROUND_HALF_UP), "f")


def linhas_lancamentos(livros: LivroCaixa) -> list[list[str]]:
    """Linhas do CSV de lançamentos (sem cabeçalho), ordenadas por ano e mês."""
    linhas: list[list[str]] = []
    for numero_ano in sorted(livros.anos):
        ano = livros.anos[numero_ano]
        for numero_mes in sorted(ano.meses):
            mes = ano.meses[numero_mes]
            for receita in mes.receitas:
                linhas.append(
                    [
                        receita.data.isoformat(),
                        "receita",
                        receita.descricao,
                        receita.categoria,
                        "",
                        formatar_decimal(receita.valor),
                    ]
                )
            for despesa in mes.despesas:
                linhas.append(
                    [
                        despesa.data.isoformat(),
                        "despesa",
                        despesa.descricao,
                        despesa.categoria,
                        "",
                        formatar_decimal(despesa.valor),
                    ]
                )
            for investimento in mes.investimentos:
                linhas.append(
                    [
                        investimento.data.isoformat(),
                        "investimento",
                        investimento.descricao,
                        investimento.categoria,
                        investimento.ativo,
                        formatar_decimal(investimento.valor),
                    ]
                )
    return linhas


def linhas_resumo(livros: LivroCaixa) -> list[list[str]]:
    """Linhas do CSV de resumo mensal (sem cabeçalho), ordenadas por ano e mês."""
    linhas: list[list[str]] = []
    for numero_ano in sorted(livros.anos):
        ano = livros.anos[numero_ano]
        for numero_mes in sorted(ano.meses):
            mes = ano.meses[numero_mes]
            linhas.append(
                [
                    str(numero_ano),
                    str(numero_mes),
                    formatar_decimal(mes.total_receitas),
                    formatar_decimal(mes.total_despesas),
                    formatar_decimal(mes.total_investimentos),
                    formatar_decimal(mes.saldo_livre),
                ]
            )
    return linhas


def _gravar(caminho: Path, cabecalho: list[str], linhas: list[list[str]]) -> None:
    with open(caminho, "w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.writer(arquivo, lineterminator="\n")
        escritor.writerow(cabecalho)
        escritor.writerows(linhas)


def exportar_csv(livros: LivroCaixa, destino_base: str | Path) -> tuple[Path, Path]:
    """Cria o diretório se necessário e grava os dois CSV em UTF-8. Retorna os caminhos."""
    lancamentos, resumo = caminhos_csv(destino_base)
    lancamentos.parent.mkdir(parents=True, exist_ok=True)
    _gravar(lancamentos, CABECALHO_LANCAMENTOS, linhas_lancamentos(livros))
    _gravar(resumo, CABECALHO_RESUMO, linhas_resumo(livros))
    return lancamentos, resumo
