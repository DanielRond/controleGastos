"""Testes de propriedade dos gráficos extras (generator.py)."""

import tempfile
from datetime import date
from decimal import Decimal
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

from controlegastos.generator import (
    _patrimonio_acumulado,
    _ranking_despesas,
    gerar_planilha,
)
from controlegastos.modelo import Despesa, Investimento, LivroCaixa

valores = st.decimals(min_value=Decimal("0.01"), max_value=Decimal("9999.99"), places=2)
categorias = st.sampled_from(["", "   ", "geral", "Moradia", "Lazer", "Saúde"])


@st.composite
def livros(draw, max_meses=4, despesas=True, investimentos=True):
    livro = LivroCaixa()
    chaves = draw(st.lists(st.tuples(st.integers(2024, 2025), st.integers(1, 12)),
                           max_size=max_meses, unique=True))
    for ano, numero in chaves:
        mes = livro.ano(ano).mes(numero)
        dia = date(ano, numero, 1)
        if despesas:
            for valor, cat in draw(st.lists(st.tuples(valores, categorias), max_size=4)):
                mes.despesas.append(Despesa("d", valor, dia, cat))
        if investimentos:
            for valor in draw(st.lists(valores, max_size=3)):
                mes.investimentos.append(Investimento("i", valor, dia, "inv", tipo="renda_fixa"))
    return livro


def _todos_meses(livro):
    return [livro.anos[a].meses[m] for a in sorted(livro.anos) for m in sorted(livro.anos[a].meses)]


# Feature: controlegastos-agentes-ia, Property 10: Ranking de despesas ordenado, completo e com rótulo padrão
@settings(max_examples=100, deadline=None)
@given(livros())
def test_ranking_ordenado_completo_e_rotulo_padrao(livro) -> None:
    ranking = _ranking_despesas(livro)
    total = sum((m.total_despesas for m in _todos_meses(livro)), Decimal(0))

    assert sum((v for _, v in ranking), Decimal(0)) == total
    assert ranking == sorted(ranking, key=lambda item: (-item[1], item[0]))
    nomes = [n for n, _ in ranking]
    assert len(nomes) == len(set(nomes))
    assert not {"", "   ", "geral"} & set(nomes)


# Feature: controlegastos-agentes-ia, Property 11: Patrimônio acumulado é a soma cumulativa dos aportes
@settings(max_examples=100, deadline=None)
@given(livros())
def test_patrimonio_e_soma_cumulativa(livro) -> None:
    patrimonio = _patrimonio_acumulado(livro)
    meses = _todos_meses(livro)

    assert len(patrimonio) == len(meses)
    acumulado = Decimal(0)
    for (rotulo, valor), mes in zip(patrimonio, meses, strict=True):
        acumulado += mes.total_investimentos
        assert valor == acumulado
    assert [r for r, _ in patrimonio] == sorted(r for r, _ in patrimonio)


# Feature: controlegastos-agentes-ia, Property 12: Gerar a planilha nunca falha por dados insuficientes
@settings(max_examples=30, deadline=None)
@given(
    st.one_of(
        st.just(LivroCaixa()),
        livros(max_meses=1),
        livros(despesas=False),
        livros(investimentos=False),
    )
)
def test_gerar_planilha_nunca_falha_com_dados_insuficientes(livro) -> None:
    with tempfile.TemporaryDirectory() as pasta:
        destino = gerar_planilha(livro, Path(pasta) / "p.xlsx")
        assert destino.exists()
