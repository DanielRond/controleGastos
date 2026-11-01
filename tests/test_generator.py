"""Testes da geração de planilhas (generator.py)."""

from pathlib import Path

from openpyxl import load_workbook

from controlegastos.generator import gerar_planilha
from controlegastos.loader import carregar_json

RAIZ = Path(__file__).resolve().parent.parent
EXEMPLO = RAIZ / "data" / "entradas" / "exemplo.json"


def test_gera_planilha_com_abas_esperadas(tmp_path: Path) -> None:
    livros = carregar_json(EXEMPLO)
    destino = gerar_planilha(livros, tmp_path / "planilha.xlsx")

    assert destino.exists()
    workbook = load_workbook(destino)
    assert workbook.sheetnames == ["Resumo Geral", "2025-01", "2025-02", "Gráficos"]


def test_resumo_geral_tem_cabecalho(tmp_path: Path) -> None:
    livros = carregar_json(EXEMPLO)
    destino = gerar_planilha(livros, tmp_path / "planilha.xlsx")

    workbook = load_workbook(destino)
    resumo = workbook["Resumo Geral"]
    assert resumo["A1"].value == "Ano"
    assert resumo["B1"].value == "Mês"


def test_aba_do_mes_tem_linha_saldo_livre(tmp_path: Path) -> None:
    livros = carregar_json(EXEMPLO)
    destino = gerar_planilha(livros, tmp_path / "planilha.xlsx")

    workbook = load_workbook(destino)
    planilha = workbook["2025-01"]
    assert planilha["A1"].value == "Data"

    saldo_celula = None
    for linha in planilha.iter_rows(min_row=2, values_only=True):
        if linha[2] == "Saldo Livre":
            saldo_celula = linha[3]
    assert saldo_celula is not None
    assert round(float(saldo_celula), 2) == 2470.00


def test_aba_graficos_tem_graficos(tmp_path: Path) -> None:
    livros = carregar_json(EXEMPLO)
    destino = gerar_planilha(livros, tmp_path / "planilha.xlsx")

    workbook = load_workbook(destino)
    graficos = workbook["Gráficos"]
    assert graficos._charts, "esperava ao menos um gráfico na aba Gráficos"
    assert len(graficos._charts) >= 2


def _livro_um_mes(com_investimento: bool):
    from datetime import date
    from decimal import Decimal

    from controlegastos.modelo import Despesa, Investimento, LivroCaixa

    livro = LivroCaixa()
    mes = livro.ano(2025).mes(1)
    mes.despesas.append(Despesa("Mercado", Decimal("10.00"), date(2025, 1, 2), "Alimentação"))
    if com_investimento:
        mes.investimentos.append(
            Investimento("Aporte", Decimal("100.00"), date(2025, 1, 3), "inv", tipo="renda_fixa")
        )
    return livro


def test_exemplo_completo_gera_cinco_graficos(tmp_path: Path) -> None:
    livros = carregar_json(RAIZ / "data" / "entradas" / "exemplo-completo.json")
    destino = gerar_planilha(livros, tmp_path / "planilha.xlsx")

    graficos = load_workbook(destino)["Gráficos"]
    assert len(graficos._charts) == 5


def test_graficos_com_eixos_visiveis_e_rotulos_do_comparativo_abaixo(tmp_path: Path) -> None:
    livros = carregar_json(RAIZ / "data" / "entradas" / "exemplo-completo.json")
    graficos = load_workbook(gerar_planilha(livros, tmp_path / "p.xlsx"))["Gráficos"]
    com_eixos = [c for c in graficos._charts if type(c).__name__ != "PieChart"]
    assert len(com_eixos) == 4
    assert all(c.x_axis.delete is False and c.y_axis.delete is False for c in com_eixos)
    comparativo = next(c for c in com_eixos if "Comparativo" in str(c.title.tx.rich.p[0].r[0].t))
    assert comparativo.x_axis.tickLblPos == "low"


def test_um_mes_com_investimento_gera_so_pizza_e_barras_mensais_e_ranking(tmp_path: Path) -> None:
    destino = gerar_planilha(_livro_um_mes(True), tmp_path / "p.xlsx")
    graficos = load_workbook(destino)["Gráficos"]
    tipos = sorted(type(c).__name__ for c in graficos._charts)
    # pizza + barras mensais + ranking (há despesa); sem patrimônio nem comparativo
    assert tipos == ["BarChart", "BarChart", "PieChart"]


def test_um_mes_sem_investimento_gera_barras_e_ranking(tmp_path: Path) -> None:
    destino = gerar_planilha(_livro_um_mes(False), tmp_path / "p.xlsx")
    graficos = load_workbook(destino)["Gráficos"]
    assert sorted(type(c).__name__ for c in graficos._charts) == ["BarChart", "BarChart"]


def test_ranking_despesas_usa_sem_categoria() -> None:
    from datetime import date
    from decimal import Decimal

    from controlegastos.generator import _ranking_despesas
    from controlegastos.modelo import Despesa, LivroCaixa

    livro = LivroCaixa()
    mes = livro.ano(2025).mes(1)
    d = date(2025, 1, 1)
    mes.despesas += [
        Despesa("a", Decimal(5), d, ""),
        Despesa("b", Decimal(3), d, "   "),
        Despesa("c", Decimal(2), d, "geral"),
        Despesa("d", Decimal(10), d, "Moradia"),
        Despesa("e", Decimal(10), d, "Lazer"),
    ]
    assert _ranking_despesas(livro) == [
        ("Lazer", Decimal(10)),
        ("Moradia", Decimal(10)),
        ("Sem categoria", Decimal(10)),
    ]
