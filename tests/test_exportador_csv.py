"""Testes unitários do exportador CSV."""

from __future__ import annotations

import csv
from datetime import date
from decimal import Decimal
from pathlib import Path

from openpyxl import load_workbook

from controlegastos.exportador_csv import (
    CABECALHO_LANCAMENTOS,
    CABECALHO_RESUMO,
    caminhos_csv,
    exportar_csv,
    formatar_decimal,
    linhas_lancamentos,
    linhas_resumo,
)
from controlegastos.generator import gerar_planilha
from controlegastos.loader import carregar_json
from controlegastos.modelo import Despesa, Investimento, LivroCaixa, Receita

EXEMPLO = Path(__file__).resolve().parent.parent / "data" / "entradas" / "exemplo.json"


def _ler(caminho: Path) -> list[list[str]]:
    with open(caminho, encoding="utf-8", newline="") as arquivo:
        return list(csv.reader(arquivo))


def test_cabecalhos_exatos(tmp_path):
    lancamentos, resumo = exportar_csv(carregar_json(EXEMPLO), tmp_path / "p.xlsx")
    assert _ler(lancamentos)[0] == ["data", "tipo", "descricao", "categoria", "ativo", "valor"]
    assert _ler(resumo)[0] == [
        "ano",
        "mes",
        "receitas",
        "despesas",
        "investimentos",
        "saldo_livre",
    ]
    assert CABECALHO_LANCAMENTOS == _ler(lancamentos)[0]
    assert CABECALHO_RESUMO == _ler(resumo)[0]


def test_formatar_decimal_duas_casas():
    assert formatar_decimal(Decimal(1200)) == "1200.00"
    assert formatar_decimal(Decimal("1234.5")) == "1234.50"
    assert formatar_decimal(Decimal(-10)) == "-10.00"
    assert formatar_decimal(Decimal(1000000)) == "1000000.00"


def test_formatar_decimal_arredonda_half_up():
    assert formatar_decimal(Decimal("0.005")) == "0.01"
    assert formatar_decimal(Decimal("0.004")) == "0.00"
    assert formatar_decimal(Decimal("2.675")) == "2.68"


def test_cria_diretorio_de_destino(tmp_path):
    destino = tmp_path / "a" / "b" / "p.xlsx"
    lancamentos, resumo = exportar_csv(LivroCaixa(), destino)
    assert lancamentos.exists()
    assert resumo.exists()


def test_utf8_com_acentos_sem_bom(tmp_path):
    livro = LivroCaixa()
    mes = livro.ano(2025).mes(1)
    mes.despesas.append(Despesa("Pão, café e açaí", Decimal(10), date(2025, 1, 2), "alimentação"))
    lancamentos, _ = exportar_csv(livro, tmp_path / "p.xlsx")
    bruto = lancamentos.read_bytes()
    assert not bruto.startswith(b"\xef\xbb\xbf")
    assert b"\r" not in bruto
    linhas = _ler(lancamentos)
    assert linhas[1] == ["2025-01-02", "despesa", "Pão, café e açaí", "alimentação", "", "10.00"]


def test_ativo_so_para_investimentos_e_ordem(tmp_path):
    livro = LivroCaixa()
    mes = livro.ano(2025).mes(1)
    mes.investimentos.append(
        Investimento("Aporte", Decimal(100), date(2025, 1, 3), "geral", tipo="fii", ativo="KNSC11")
    )
    mes.despesas.append(Despesa("Luz", Decimal(50), date(2025, 1, 2), "casa"))
    mes.receitas.append(Receita("Freela", Decimal(20), date(2025, 1, 1), "extra"))
    linhas = linhas_lancamentos(livro)
    assert [x[1] for x in linhas] == ["receita", "despesa", "investimento"]
    assert [x[4] for x in linhas] == ["", "", "KNSC11"]


def test_nomes_derivados_de_o():
    assert caminhos_csv("saida/planilha.xlsx") == (
        Path("saida/planilha-lancamentos.csv"),
        Path("saida/planilha-resumo-mensal.csv"),
    )
    assert caminhos_csv("saida/jan") == (
        Path("saida/jan-lancamentos.csv"),
        Path("saida/jan-resumo-mensal.csv"),
    )


def test_resumo_do_exemplo_coincide_com_modelo():
    livro = carregar_json(EXEMPLO)
    linhas = linhas_resumo(livro)
    jan = next(x for x in linhas if x[0] == "2025" and x[1] == "1")
    assert jan[5] == "2470.00"
    esperado = [
        [
            str(a),
            str(m),
            formatar_decimal(livro.anos[a].meses[m].total_receitas),
            formatar_decimal(livro.anos[a].meses[m].total_despesas),
            formatar_decimal(livro.anos[a].meses[m].total_investimentos),
            formatar_decimal(livro.anos[a].meses[m].saldo_livre),
        ]
        for a in sorted(livro.anos)
        for m in sorted(livro.anos[a].meses)
    ]
    assert linhas == esperado


def test_saldo_do_csv_igual_ao_resumo_geral_do_xlsx(tmp_path):
    livro = carregar_json(EXEMPLO)
    planilha = gerar_planilha(livro, tmp_path / "p.xlsx")
    _, resumo = exportar_csv(livro, tmp_path / "p.xlsx")

    aba = load_workbook(planilha)["Resumo Geral"]
    saldos_xlsx = [
        Decimal(str(aba.cell(row=r, column=6).value)).quantize(Decimal("0.01"))
        for r in range(2, aba.max_row + 1)
        if isinstance(aba.cell(row=r, column=1).value, int)
    ]
    saldos_csv = [Decimal(x[5]) for x in _ler(resumo)[1:]]
    assert saldos_csv == saldos_xlsx
