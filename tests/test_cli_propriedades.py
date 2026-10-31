"""Teste de propriedade: entrada inválida é rejeitada antes de qualquer geração."""

import json
import sys
import tempfile
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from controlegastos.cli import main
from controlegastos.loader import ErroDeValidacaoJSON, carregar_dados

# Violações conhecidas aplicadas a um mês válido.
_VIOLACOES = [
    ("mes", 13),
    ("mes", 0),
    ("salario", True),
    ("meta_investimento", "100"),
    ("despesas", [{"descricao": "x", "valor": "1", "dia": 1}]),
    ("despesas", [{"descricao": "x", "valor": 1, "dia": 40}]),
    ("receitas", [{"valor": 1, "dia": 1}]),
    ("investimentos", [{"tipo": "acoes", "descricao": "x", "valor": 1, "dia": 1}]),
]


@st.composite
def documentos_invalidos(draw):
    escolhidas = draw(st.lists(st.sampled_from(_VIOLACOES), min_size=1, max_size=3))
    mes = {"mes": 1, "salario": 1000}
    for campo, valor in escolhidas:
        mes[campo] = valor
    return {"anos": [{"ano": 2025, "meses": [mes]}]}


# Feature: controlegastos-agentes-ia, Property 4: Entrada inválida é rejeitada antes da construção e o CLI retorna 1
@settings(max_examples=100, deadline=None)
@given(documentos_invalidos(), st.sampled_from(["xlsx", "csv", "ambos"]))
def test_entrada_invalida_rejeitada_e_cli_retorna_1(dados, formato) -> None:
    with pytest.raises(ErroDeValidacaoJSON) as info:
        carregar_dados(dados)
    assert info.value.erros

    with tempfile.TemporaryDirectory() as pasta:
        base = Path(pasta)
        entrada = base / "entrada.json"
        entrada.write_text(json.dumps(dados), encoding="utf-8")
        destino = base / "saida" / "p.xlsx"
        argv_original = sys.argv
        sys.argv = ["controlegastos", "gerar", str(entrada), "-o", str(destino), "--formato", formato]
        try:
            assert main() == 1
        finally:
            sys.argv = argv_original
        assert not (base / "saida").exists()
