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
from openpyxl.chart import BarChart, PieChart, Reference
from openpyxl.chart.label import DataLabelList
from openpyxl.chart.series import DataPoint
from openpyxl.styles import Alignment, Font, PatternFill

from .modelo import LivroCaixa, Mes

logger = logging.getLogger(__name__)

_HEADER_FILL = PatternFill("solid", fgColor="1F4E79")
_HEADER_FONT = Font(color="FFFFFF", bold=True)
_GERAL_FILL = PatternFill("solid", fgColor="D9E1F2")
_SEPARADOR_FONT = Font(bold=True)
_META_FILL = PatternFill("solid", fgColor="FFF2CC")

_TIPO_LABEL = {
    "renda_fixa": "Renda Fixa",
    "fii": "Fundos Imobiliários",
    "fiis": "Fundos Imobiliários",
    "cripto": "Criptomoedas",
    "criptomoedas": "Criptomoedas",
}

_TIPO_COR = {
    "renda_fixa": "1F4E79",
    "fii": "2E75B6",
    "fiis": "2E75B6",
    "cripto": "C00000",
    "criptomoedas": "C00000",
}

_COR_FALLBACK = "808080"


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


def _agrupar_por_tipo(mes: Mes) -> dict[str, Decimal]:
    por_tipo: dict[str, Decimal] = {}
    for item in mes.investimentos:
        chave = item.tipo or item.categoria
        por_tipo[chave] = por_tipo.get(chave, Decimal(0)) + item.valor
    return por_tipo


def _renderizar_investimentos(sheet, linha: int, mes: Mes) -> int:
    total = mes.total_investimentos
    por_tipo = _agrupar_por_tipo(mes)

    for item in sorted(mes.investimentos, key=lambda t: (t.tipo, t.data, t.descricao)):
        coluna_categoria = item.ativo or _TIPO_LABEL.get(item.tipo or "", item.tipo or item.categoria)
        _linha_transacao(sheet, linha, item.data, item.descricao, coluna_categoria, item.valor)
        if total:
            pct = item.valor * 100 / total
            sheet.cell(row=linha, column=5, value=float(round(pct, 2))).number_format = "0.00"
        linha += 1

    _linha_total(sheet, linha, "Total Investimentos", total)
    linha += 1

    for tipo, subtotal in sorted(por_tipo.items()):
        if not total:
            continue
        label = _TIPO_LABEL.get(tipo, tipo)
        pct = subtotal * 100 / total
        rotulo = f"{label} ({tipo})"
        sheet.cell(row=linha, column=3, value=rotulo).font = Font(bold=True, italic=True)
        celula = sheet.cell(row=linha, column=4, value=float(subtotal))
        celula.font = Font(bold=True, italic=True)
        celula.number_format = "#,##0.00"
        pct_celula = sheet.cell(row=linha, column=5, value=float(round(pct, 2)))
        pct_celula.font = Font(bold=True, italic=True)
        pct_celula.number_format = "0.00"
        linha += 1

    if mes.meta_investimento:
        saldo_meta = mes.meta_investimento - total
        sheet.cell(row=linha, column=3, value="Meta de Investimento").font = _SEPARADOR_FONT
        sheet.cell(row=linha, column=3).fill = _META_FILL
        celula = sheet.cell(row=linha, column=4, value=float(mes.meta_investimento))
        celula.font = _SEPARADOR_FONT
        celula.fill = _META_FILL
        celula.number_format = "#,##0.00"
        linha += 1
        sheet.cell(row=linha, column=3, value="Falta investir (meta)" if saldo_meta > 0 else "Acima da meta").font = _SEPARADOR_FONT
        sheet.cell(row=linha, column=3).fill = _META_FILL
        celula = sheet.cell(row=linha, column=4, value=float(saldo_meta))
        celula.font = _SEPARADOR_FONT
        celula.fill = _META_FILL
        celula.number_format = "#,##0.00"
        linha += 1

    return linha


def _renderizar_mes(sheet, mes: Mes) -> None:
    _configurar_colunas(sheet)
    _cabecalho(sheet, ["Data", "Descrição", "Categoria", "Valor", "% do Total Investido"])
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
    linha = _renderizar_investimentos(sheet, linha, mes)
    linha += 1

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


def _dados_mensais(livros: LivroCaixa) -> list[tuple[str, float, float, float, float]]:
    dados = []
    for numero_ano in sorted(livros.anos):
        ano = livros.anos[numero_ano]
        for numero_mes in sorted(ano.meses):
            mes = ano.meses[numero_mes]
            dados.append(
                (
                    f"{numero_ano}-{numero_mes:02d}",
                    float(mes.total_receitas),
                    float(mes.total_despesas),
                    float(mes.total_investimentos),
                    float(mes.saldo_livre),
                )
            )
    return dados


def _classe_agregada(livros: LivroCaixa) -> dict[str, Decimal]:
    totais: dict[str, Decimal] = {}
    for ano in livros.anos.values():
        for mes in ano.meses.values():
            for tipo, subtotal in _agrupar_por_tipo(mes).items():
                totais[tipo] = totais.get(tipo, Decimal(0)) + subtotal
    return totais


def _renderizar_graficos(workbook: Workbook, livros: LivroCaixa) -> None:
    """Cria a aba "Gráficos" com pizza por classe de investimento e barras mensais.

    Os valores reais ficam em tabelas de apoio (colunas à direita); os gráficos
    apontam para elas, então refletem fielmente os dados das abas anteriores.
    """
    mensais = _dados_mensais(livros)
    por_classe = _classe_agregada(livros)
    if not mensais:
        return

    planilha = workbook.create_sheet("Gráficos")
    planilha.column_dimensions["A"].width = 2
    planilha.column_dimensions["B"].width = 16
    planilha.column_dimensions["P"].width = 2
    planilha.column_dimensions["Q"].width = 12
    planilha.column_dimensions["R"].width = 14
    planilha.column_dimensions["S"].width = 14
    planilha.column_dimensions["T"].width = 14
    planilha.column_dimensions["U"].width = 14

    col_mes = 17
    cabecalho = ["Mês", "Receitas", "Despesas", "Investimentos", "Saldo Livre"]
    for i, nome in enumerate(cabecalho, start=col_mes):
        planilha.cell(row=1, column=i, value=nome)
    for i, (mes, receitas, despesas, investimentos, saldo) in enumerate(mensais, start=2):
        planilha.cell(row=i, column=col_mes, value=mes)
        for j, valor in enumerate([receitas, despesas, investimentos, saldo], start=col_mes + 1):
            celula = planilha.cell(row=i, column=j, value=valor)
            celula.number_format = "#,##0.00"

    if por_classe:
        linha_inicial = len(mensais) + 3
        planilha.cell(row=linha_inicial, column=col_mes, value="Tipo")
        planilha.cell(row=linha_inicial, column=col_mes + 1, value="Valor")
        for i, (tipo, subtotal) in enumerate(sorted(por_classe.items()), start=linha_inicial + 1):
            planilha.cell(row=i, column=col_mes, value=_TIPO_LABEL.get(tipo, tipo))
            celula = planilha.cell(row=i, column=col_mes + 1, value=float(subtotal))
            celula.number_format = "#,##0.00"

        pie = PieChart()
        pie.title = "Investimentos por Classe (total do período)"
        labels = Reference(planilha, min_col=col_mes, min_row=linha_inicial + 1, max_row=linha_inicial + len(por_classe))
        dados_pie = Reference(planilha, min_col=col_mes + 1, min_row=linha_inicial, max_row=linha_inicial + len(por_classe))
        pie.add_data(dados_pie, titles_from_data=True)
        pie.set_categories(labels)
        pie.dataLabels = DataLabelList()
        pie.dataLabels.showPercent = True
        serie = pie.series[0]
        for idx, (tipo, _) in enumerate(sorted(por_classe.items())):
            ponto = DataPoint(idx=idx)
            ponto.graphicalProperties.solidFill = _TIPO_COR.get(tipo, _COR_FALLBACK)
            serie.data_points.append(ponto)
        planilha.add_chart(pie, "A2")

    bar = BarChart()
    bar.type = "col"
    bar.grouping = "clustered"
    bar.title = "Por Mês: Receitas, Despesas, Investimentos e Saldo Livre"
    bar.x_axis.title = "Mês"
    bar.y_axis.title = "Valor"
    dados_bar = Reference(planilha, min_col=col_mes + 1, min_row=1, max_col=col_mes + 4, max_row=len(mensais) + 1)
    bar.add_data(dados_bar, titles_from_data=True)
    categorias = Reference(planilha, min_col=col_mes, min_row=2, max_row=len(mensais) + 1)
    bar.set_categories(categorias)
    planilha.add_chart(bar, "A22")


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

    _renderizar_graficos(workbook, livros)
    workbook.save(destino)
    logger.info("Planilha gerada em %s", destino)
    return destino