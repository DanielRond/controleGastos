"""Testes de propriedade do exportador CSV."""

from __future__ import annotations

import csv
import tempfile
from datetime import date
from decimal import Decimal
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st
from openpyxl import load_workbook

from controlegastos.exportador_csv import exportar_csv, formatar_decimal
from controlegastos.generator import gerar_planilha
from controlegastos.modelo import Despesa, Investimento, LivroCaixa, Receita

# Textos com vírgula, aspas, quebra de linha e Unicode (sem surrogates nem NUL).
_textos = st.text(
    alphabet=st.one_of(
        st.sampled_from(list(',"\n\r;áéçãñ€日本 ')),
        st.characters(blacklist_categories=("Cs",), blacklist_characters="\x00"),
    ),
    max_size=12,
)
# A Property 6 grava no .xlsx, que rejeita caracteres de controle; textos simples bastam.
_textos_simples = st.text(alphabet="abc áç", max_size=5)
_valores = st.decimals(
    min_value=Decimal(0), max_value=Decimal(100000), places=2, allow_nan=False
)
_valores_finos = st.decimals(
    min_value=Decimal(0), max_value=Decimal(100000), places=4, allow_nan=False
)


@st.composite
def _livros(draw, valores=_valores, textos=_textos):
    livro = LivroCaixa()
    for numero_ano in draw(st.lists(st.sampled_from([2024, 2025]), max_size=2, unique=True)):
        ano = livro.ano(numero_ano)
        for numero_mes in draw(st.lists(st.integers(1, 12), max_size=3, unique=True)):
            mes = ano.mes(numero_mes)
            dia = st.integers(1, 28)
            for _ in range(draw(st.integers(0, 2))):
                mes.receitas.append(
                    Receita(
                        draw(textos),
                        draw(valores),
                        date(numero_ano, numero_mes, draw(dia)),
                        draw(textos),
                    )
                )
            for _ in range(draw(st.integers(0, 2))):
                mes.despesas.append(
                    Despesa(
                        draw(textos),
                        draw(valores),
                        date(numero_ano, numero_mes, draw(dia)),
                        draw(textos),
                    )
                )
            for _ in range(draw(st.integers(0, 2))):
                mes.investimentos.append(
                    Investimento(
                        draw(textos),
                        draw(valores),
                        date(numero_ano, numero_mes, draw(dia)),
                        draw(textos),
                        tipo="fii",
                        ativo=draw(textos),
                    )
                )
    return livro


def _ler(caminho: Path) -> list[list[str]]:
    with open(caminho, encoding="utf-8", newline="") as arquivo:
        return list(csv.reader(arquivo))


# Spec: EXP-11, EXP-05 (propriedade: Round trip do CSV de lançamentos)
@settings(max_examples=100, deadline=None)
@given(livro=_livros())
def test_round_trip_csv_de_lancamentos(livro):
    with tempfile.TemporaryDirectory() as tmp:
        lancamentos, _ = exportar_csv(livro, Path(tmp) / "saida" / "p.xlsx")
        lidas = _ler(lancamentos)[1:]

    esperadas = []
    for numero_ano in sorted(livro.anos):
        for numero_mes in sorted(livro.anos[numero_ano].meses):
            mes = livro.anos[numero_ano].meses[numero_mes]
            for tipo, itens in (
                ("receita", mes.receitas),
                ("despesa", mes.despesas),
                ("investimento", mes.investimentos),
            ):
                for item in itens:
                    ativo = item.ativo if tipo == "investimento" else ""
                    esperadas.append(
                        (
                            item.data,
                            tipo,
                            item.descricao,
                            item.categoria,
                            ativo,
                            item.valor,
                        )
                    )

    assert len(lidas) == len(esperadas)
    for linha, (data, tipo, descricao, categoria, ativo, valor) in zip(lidas, esperadas):
        assert date.fromisoformat(linha[0]) == data
        assert linha[1] == tipo
        assert linha[2] == descricao
        assert linha[3] == categoria
        assert linha[4] == ativo
        assert Decimal(linha[5]) == valor


# Spec: EXP-08, EXP-04 (propriedade: Totais do CSV de resumo coincidem com o modelo e com o Resumo Geral)
@settings(max_examples=100, deadline=None)
@given(livro=_livros(_valores_finos, _textos_simples))
def test_totais_do_resumo_coincidem_com_modelo_e_resumo_geral(livro):
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp) / "p.xlsx"
        planilha = gerar_planilha(livro, base)
        _, resumo = exportar_csv(livro, base)
        linhas = _ler(resumo)[1:]
        aba = load_workbook(planilha)["Resumo Geral"]
        saldos_xlsx = [
            Decimal(str(aba.cell(row=r, column=6).value)).quantize(Decimal("0.01"))
            for r in range(2, aba.max_row + 1)
            if isinstance(aba.cell(row=r, column=1).value, int)
        ]

    meses = [
        livro.anos[a].meses[m] for a in sorted(livro.anos) for m in sorted(livro.anos[a].meses)
    ]
    assert len(linhas) == len(meses) == len(saldos_xlsx)
    for linha, mes, saldo_xlsx in zip(linhas, meses, saldos_xlsx):
        assert (int(linha[0]), int(linha[1])) == (mes.ano, mes.numero)
        assert linha[2] == formatar_decimal(mes.total_receitas)
        assert linha[3] == formatar_decimal(mes.total_despesas)
        assert linha[4] == formatar_decimal(mes.total_investimentos)
        assert linha[5] == formatar_decimal(mes.saldo_livre)
        # Convenção: receitas - despesas - investimentos
        assert mes.saldo_livre == mes.total_receitas - mes.total_despesas - mes.total_investimentos
        assert abs(Decimal(linha[5]) - saldo_xlsx) <= Decimal("0.01")
