"""Testes da geração de planilhas (generator.py)."""

from pathlib import Path

import pytest
from openpyxl import load_workbook

from controlegastos.generator import gerar_planilha
from controlegastos.loader import carregar_json

RAIZ = Path(__file__).resolve().parent.parent
EXEMPLO = RAIZ / "data" / "entradas" / "exemplo.json"


# Spec: PLN-01
def test_gera_planilha_com_abas_esperadas(tmp_path: Path) -> None:
    livros = carregar_json(EXEMPLO)
    destino = gerar_planilha(livros, tmp_path / "planilha.xlsx")

    assert destino.exists()
    workbook = load_workbook(destino)
    assert workbook.sheetnames == ["Resumo Geral", "2025-01", "2025-02", "Gráficos"]


# Spec: PLN-02
def test_resumo_geral_tem_cabecalho(tmp_path: Path) -> None:
    livros = carregar_json(EXEMPLO)
    destino = gerar_planilha(livros, tmp_path / "planilha.xlsx")

    workbook = load_workbook(destino)
    resumo = workbook["Resumo Geral"]
    assert resumo["A1"].value == "Ano"
    assert resumo["B1"].value == "Mês"


# Spec: PLN-03
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


# Spec: PLN-05
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


# Spec: PLN-05, PLN-06, PLN-07, PLN-08
def test_exemplo_completo_gera_cinco_graficos(tmp_path: Path) -> None:
    livros = carregar_json(RAIZ / "data" / "entradas" / "exemplo-completo.json")
    destino = gerar_planilha(livros, tmp_path / "planilha.xlsx")

    graficos = load_workbook(destino)["Gráficos"]
    assert len(graficos._charts) == 5


# Spec: PLN-10
def test_graficos_com_eixos_visiveis_e_rotulos_do_comparativo_abaixo(tmp_path: Path) -> None:
    livros = carregar_json(RAIZ / "data" / "entradas" / "exemplo-completo.json")
    graficos = load_workbook(gerar_planilha(livros, tmp_path / "p.xlsx"))["Gráficos"]
    com_eixos = [c for c in graficos._charts if type(c).__name__ != "PieChart"]
    assert len(com_eixos) == 4
    assert all(c.x_axis.delete is False and c.y_axis.delete is False for c in com_eixos)
    comparativo = next(c for c in com_eixos if "Comparativo" in str(c.title.tx.rich.p[0].r[0].t))
    assert comparativo.x_axis.tickLblPos == "low"


# Spec: PLN-05, PLN-09
def test_um_mes_com_investimento_gera_so_pizza_e_barras_mensais_e_ranking(tmp_path: Path) -> None:
    destino = gerar_planilha(_livro_um_mes(True), tmp_path / "p.xlsx")
    graficos = load_workbook(destino)["Gráficos"]
    tipos = sorted(type(c).__name__ for c in graficos._charts)
    # pizza + barras mensais + ranking (há despesa); sem patrimônio nem comparativo
    assert tipos == ["BarChart", "BarChart", "PieChart"]


# Spec: PLN-09
def test_um_mes_sem_investimento_gera_barras_e_ranking(tmp_path: Path) -> None:
    destino = gerar_planilha(_livro_um_mes(False), tmp_path / "p.xlsx")
    graficos = load_workbook(destino)["Gráficos"]
    assert sorted(type(c).__name__ for c in graficos._charts) == ["BarChart", "BarChart"]


# Spec: PLN-07
def test_ranking_despesas_usa_sem_categoria() -> None:
    from datetime import date
    from decimal import Decimal

    from controlegastos.modelo import Despesa, LivroCaixa
    from controlegastos.resumo import ranking_despesas

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
    assert ranking_despesas(livro) == [
        ("Lazer", Decimal(10)),
        ("Moradia", Decimal(10)),
        ("Sem categoria", Decimal(10)),
    ]


# Spec: PLN-04
def test_aba_do_mes_mostra_ativo_percentuais_por_classe_e_meta(tmp_path: Path) -> None:
    livros = carregar_json(RAIZ / "data" / "entradas" / "exemplo-completo.json")
    aba = load_workbook(gerar_planilha(livros, tmp_path / "p.xlsx"))["2025-01"]
    linhas = [v for v in ([c.value for c in linha if c.value is not None] for linha in aba.iter_rows()) if v]

    btc = next(v for v in linhas if "BTC" in v and "Janeiro: BTC" in v)
    assert btc[-1] == pytest.approx(10.47, abs=0.01)  # ativo na coluna Categoria e % do total
    por_classe = {v[0].split(" (")[0]: v[-1] for v in linhas if str(v[0]).endswith(("(cripto)", "(fii)", "(renda_fixa)"))}
    assert por_classe == pytest.approx(
        {"Criptomoedas": 14.95, "Fundos Imobiliários": 25.20, "Renda Fixa": 59.85}, abs=0.01
    )
    meta = next(v for v in linhas if v[0] == "Meta de Investimento")
    falta = next(v for v in linhas if str(v[0]).startswith("Falta investir"))
    assert meta[-1] == pytest.approx(850.00)
    assert falta[-1] == pytest.approx(105.22, abs=0.01)


# Spec: PLN-11
def test_graficos_sao_alimentados_por_area_de_apoio_a_partir_da_coluna_q(tmp_path: Path) -> None:
    graficos = load_workbook(gerar_planilha(carregar_json(EXEMPLO), tmp_path / "p.xlsx"))["Gráficos"]
    cabecalho = [graficos.cell(1, coluna).value for coluna in range(17, 22)]
    assert cabecalho == ["Mês", "Receitas", "Despesas", "Investimentos", "Saldo Livre"]


# Spec: PLN-12
def test_planilha_em_memoria_tem_o_mesmo_conteudo_da_gerada_em_arquivo(tmp_path: Path) -> None:
    from io import BytesIO

    from controlegastos.generator import gerar_planilha_bytes

    livros = carregar_json(RAIZ / "data" / "entradas" / "exemplo-completo.json")
    arquivo = load_workbook(gerar_planilha(livros, tmp_path / "p.xlsx"))
    memoria = load_workbook(BytesIO(gerar_planilha_bytes(livros)))

    assert memoria.sheetnames == arquivo.sheetnames
    for nome in arquivo.sheetnames:
        celulas = lambda aba: {
            (c.coordinate, c.value, c.number_format) for linha in aba.iter_rows() for c in linha if c.value is not None
        }
        assert celulas(memoria[nome]) == celulas(arquivo[nome]), nome
    assert len(memoria["Gráficos"]._charts) == len(arquivo["Gráficos"]._charts) == 5
    assert not list(tmp_path.glob("*.tmp"))


# Spec: PLN-12
def test_planilha_em_memoria_nao_escreve_em_disco(tmp_path: Path, monkeypatch) -> None:
    from controlegastos.generator import gerar_planilha_bytes

    monkeypatch.chdir(tmp_path)
    assert gerar_planilha_bytes(carregar_json(EXEMPLO)).startswith(b"PK")  # zip/xlsx
    assert list(tmp_path.iterdir()) == []
