"""Gerador de planilhas (xlsx) a partir do LivroCaixa.

Estrutura do arquivo gerado:
- Aba "Resumo Geral": totais por ano (receitas, despesas, investimentos, saldo)
- Uma aba por mês "AAAA-MM": receitas, despesas, investimentos e saldo livre
"""

from __future__ import annotations

import calendar
import logging
from decimal import Decimal
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill

from .modelo import LivroCaixa, Mes

logger = logging.getLogger(__name__)

_HEADER_FILL = PatternFill("solid", fgColor="1F4E79")
_HEADER_FONT = Font(color="FFFFFF", bold=True)
_GERAL_FILL = PatternFill("solid", fgColor="D9E1F2")
_TIPO_FILL = PatternFill("solid", fgColor="F2F2F2")
_SEPARADOR_FONT = Font(bold=True)

_COLUNAS = {"DATA": "A", "DESCRICAO": "B", "CATEGORIA": "C", "VALOR": "D"}


def _configurar_colunas(sheet) -> None:
    sheet.column_dimensions["A"].width = 12
    sheet.column_dimensions["B"].width = 42
    sheet.column_dimensions["C"].width = 18
    sheet.column_dimensions["D"].width = 16
    sheet.column_dimensions["E"].width = 16


def _cabecalho(sheet, colunas: list[str]) -> None:
    for i, nome in enumerate(colunas, start=1):
        celula = sheet.cell(row=1, column=i, value=nome)
        celula.font = _HEADER_FONT
        celula.fill = _HEADER_FILL
        celula.alignment = Alignment(horizontal="center")


def _secao(sheet, linha: int, titulo: str) -> int:
    celula = sheet.cell(row=linha, column=1, value=titulo.upper())
    celula.font = _SEPARADOR_FONT
    celula.fill = _GERAL_FILL
    return linha + 1


def _linha_transacao(sheet, linha: int, data, descricao, categoria, valor) -> None:
    sheet.cell(row=linha, column=1, value=data.strftime("%d/%m/%Y"))
    sheet.cell(row=linha, column=2, value=descricao)
    sheet.cell(row=linha, column=3, value=categoria)
    sheet.cell(row=linha, column=4, value=float(valor)).number_format = "#,##0.00"


def _linha_total(sheet, linha: int, rotulo: str, valor: Decimal) -> None:
    sheet.cell(row=linha, column=3, value=rotulo).font = _SEPARADOR_FONT
    celula = sheet.cell(row=linha, column=4, value=float(valor))
    celula.font = _SEPARADOR_FONT
    celula.number_format = "#,##0.00"


def _renderizar_mes(sheet, mes: Mes) -> None:
    _configurar_colunas(sheet)
    _cabecalho(sheet, ["Data", "Descrição", "Categoria", "Valor"])
    linha = 2

    linha = _secao(sheet, linha, "Receitas")
    for item in sorted(mes.receitas, key=lambda t: t.data):
        _linha_transacao(sheet, linha, item.data, item.descricao, item.categoria, item.valor)
        linha += 1
    _linha_total(sheet, linha, "Total Receitas", mes.total_receitas)
    linha += 2

    linha = _secao(sheet, linha, "Despesas")
    for item in sorted(mes.despesas, key=lambda t: t.data):
        _linha_transacao(sheet, linha, item.data, item.descricao, item.categoria, item.valor)
        linha += 1
    _linha_total(sheet, linha, "Total Despesas", mes.total_despesas)
    linha += 2

    linha = _secao(sheet, linha, "Investimentos")
    for item in sorted(mes.investimentos, key=lambda t: t.data):
        _linha_transacao(sheet, linha, item.data, item.descricao, item.tipo or item.categoria, item.valor)
        linha += 1
    _linha_total(sheet, linha, "Total Investimentos", mes.total_investimentos)
    linha += 2

    _linha_total(sheet, linha, "Saldo Livre", mes.saldo_livre)


def _renderizar_resumo(sheet, livros: LivroCaixa) -> None:
    _configurar_colunas(sheet)
    _cabecalho(sheet, ["Ano", "Mês", "Receitas", "Despesas", "Investimentos", "Saldo Livre"])
    linha = 2
    for numero_ano in sorted(livros.anos):
        ano = livros.anos[numero_ano]
        for numero_mes in sorted(ano.meses):
            mes = ano.meses[numero_mes]
            valores = [
                mes.total_receitas,
                mes.total_despesas,
                mes.total_investimentos,
                mes.saldo_livre,
            ]
            mes_nome = f"{calendar.month_name[numero_mes]} {numero_ano}"
            sheet.cell(row=linha, column=1, value=numero_ano)
            sheet.cell(row=linha, column=2, value=mes_nome)
            for col, valor in zip(range(3, 7), valores):
                celula = sheet.cell(row=linha, column=col, value=float(valor))
                celula.number_format = "#,##0.00"
            linha += 1
        totais = [ano.total_receitas, ano.total_despesas, ano.total_investimentos]
        sheet.cell(row=linha, column=2, value=f"TOTAL {numero_ano}").font = _SEPARADOR_FONT
        for col, valor in zip(range(3, 7), totais):
            celula = sheet.cell(row=linha, column=col, value=float(valor))
            celula.number_format = "#,##0.00"
            celula.font = _SEPARADOR_FONT
        linha += 2


def gerar_planilha(livros: LivroCaixa, destino: str | Path) -> Path:
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)

    workbook = Workbook()
    resumo = workbook.active
    resumo.title = "Resumo Geral"
    _renderizar_resumo(resumo, livros)

    for numero_ano in sorted(livros.anos):
        ano = livros.anos[numero_ano]
        for numero_mes in sorted(ano.meses):
            mes = ano.meses[numero_mes]
            nome = f"{numero_ano}-{numero_mes:02d}"
            if nome in workbook.sheetnames:
                continue
            planilha = workbook.create_sheet(nome)
            _renderizar_mes(planilha, mes)

    workbook.save(destino)
    logger.info("Planilha gerada em %s", destino)
    return destino