"""Dados derivados do livro-caixa para gráficos e painéis.

Funções puras, sem dependência de openpyxl nem de qualquer interface: alimentam a
planilha (generator.py) e podem alimentar qualquer outro consumidor. Valores sempre
em Decimal.
"""

from __future__ import annotations

from decimal import Decimal

from .modelo import LivroCaixa, Mes

SEM_CATEGORIA = "Sem categoria"
TOP_RANKING = 10


def meses_ordenados(livros: LivroCaixa) -> list[tuple[str, Mes]]:
    """Meses em ordem cronológica, com o rótulo AAAA-MM."""
    resultado = []
    for numero_ano in sorted(livros.anos):
        ano = livros.anos[numero_ano]
        for numero_mes in sorted(ano.meses):
            resultado.append((f"{numero_ano}-{numero_mes:02d}", ano.meses[numero_mes]))
    return resultado


def patrimonio_acumulado(livros: LivroCaixa) -> list[tuple[str, Decimal]]:
    """Soma acumulada dos aportes (total de investimentos) mês a mês."""
    acumulado = Decimal(0)
    resultado = []
    for rotulo, mes in meses_ordenados(livros):
        acumulado += mes.total_investimentos
        resultado.append((rotulo, acumulado))
    return resultado


def ranking_despesas(livros: LivroCaixa) -> list[tuple[str, Decimal]]:
    """Total de despesas por categoria, do maior para o menor (desempate por nome)."""
    totais: dict[str, Decimal] = {}
    for _, mes in meses_ordenados(livros):
        for despesa in mes.despesas:
            nome = (despesa.categoria or "").strip()
            if not nome or nome.lower() == "geral":
                nome = SEM_CATEGORIA
            totais[nome] = totais.get(nome, Decimal(0)) + despesa.valor
    return sorted(totais.items(), key=lambda item: (-item[1], item[0]))


def variacao_saldo(livros: LivroCaixa) -> list[tuple[str, Decimal]]:
    """Saldo livre do mês menos o do mês anterior, a partir do segundo mês."""
    meses = meses_ordenados(livros)
    return [
        (rotulo, mes.saldo_livre - meses[i - 1][1].saldo_livre)
        for i, (rotulo, mes) in enumerate(meses)
        if i > 0
    ]
