"""Dados públicos dos gráficos (resumo.py), independentes do openpyxl."""

import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

from controlegastos.resumo import patrimonio_acumulado, ranking_despesas, variacao_saldo

from controlegastos.loader import carregar_json
from controlegastos.modelo import Despesa, Investimento, LivroCaixa

RAIZ = Path(__file__).resolve().parent.parent
EXEMPLO = RAIZ / "data" / "entradas" / "exemplo.json"


# Spec: PLN-13, PLN-06
def test_patrimonio_acumulado_do_exemplo_soma_os_aportes_em_decimal() -> None:
    patrimonio = patrimonio_acumulado(carregar_json(EXEMPLO))

    assert patrimonio == [("2025-01", Decimal("1000.00")), ("2025-02", Decimal("2000.00"))]
    assert all(isinstance(valor, Decimal) for _, valor in patrimonio)


# Spec: PLN-13, PLN-08
def test_variacao_saldo_e_a_diferenca_para_o_mes_anterior() -> None:
    # saldo livre: jan 2470.00, fev 2600.00
    assert variacao_saldo(carregar_json(EXEMPLO)) == [("2025-02", Decimal("130.00"))]


# Spec: PLN-13, PLN-07
def test_ranking_do_exemplo_soma_o_total_de_despesas_em_ordem_decrescente() -> None:
    livro = carregar_json(EXEMPLO)
    ranking = ranking_despesas(livro)

    totais = [valor for _, valor in ranking]
    assert totais == sorted(totais, reverse=True)
    assert sum(totais, Decimal(0)) == Decimal("3180.00")  # 1780.00 (jan) + 1400.00 (fev)


# Spec: PLN-13, PLN-09
def test_livro_vazio_ou_com_um_mes_nao_quebra() -> None:
    assert patrimonio_acumulado(LivroCaixa()) == []
    assert ranking_despesas(LivroCaixa()) == []
    assert variacao_saldo(LivroCaixa()) == []

    livro = LivroCaixa()
    mes = livro.ano(2025).mes(1)
    mes.despesas.append(Despesa("x", Decimal("5.00"), date(2025, 1, 2), "geral"))
    mes.investimentos.append(Investimento("y", Decimal("7.00"), date(2025, 1, 3), "geral", tipo="fii"))
    assert variacao_saldo(livro) == []
    assert patrimonio_acumulado(livro) == [("2025-01", Decimal("7.00"))]
    assert ranking_despesas(livro) == [("Sem categoria", Decimal("5.00"))]


# Spec: PLN-13
def test_resumo_nao_depende_do_openpyxl() -> None:
    import importlib

    for nome in [m for m in sys.modules if m.startswith("openpyxl")]:
        del sys.modules[nome]
    sys.modules.pop("controlegastos.resumo", None)
    importlib.import_module("controlegastos.resumo")

    assert not any(m.startswith("openpyxl") for m in sys.modules)
