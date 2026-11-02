"""Propriedades do armazenamento: centavos, ida e volta do JSON e lixeira."""

import csv
import io
from decimal import Decimal

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

pytest.importorskip("sqlalchemy")

from test_validador_propriedades import documentos_validos

from controlegastos.armazenamento import (
    Repositorio,
    aplicar_migracoes,
    criar_engine,
    criar_sessao,
    criar_usuario,
)
from controlegastos.armazenamento.centavos import (
    de_centavos,
    para_centavos,
)
from controlegastos.exportador_csv import exportar_csv_bytes
from controlegastos.loader import carregar_dados


def _repo_novo():
    motor = criar_engine("sqlite://")
    aplicar_migracoes(motor)
    sessao = criar_sessao(motor)
    return motor, sessao, Repositorio(sessao, criar_usuario(sessao, "ana", "h"))


def _sem_moeda(doc: dict) -> dict:
    doc = dict(doc)
    doc.pop("moeda", None)  # a moeda não é guardada no banco (BRL fixo)
    return doc


# Feature: armazenamento, STO-02: Decimal com 2 casas -> centavos -> Decimal é identidade
# Spec: STO-02
@settings(max_examples=200)
@given(st.decimals(min_value=Decimal("-1e12"), max_value=Decimal("1e12"), places=2))
def test_decimal_centavos_decimal_e_identidade(valor: Decimal) -> None:
    assert de_centavos(para_centavos(valor)) == valor


# Spec: STO-02
@settings(max_examples=200)
@given(st.integers(min_value=-(10**14), max_value=10**14))
def test_centavos_decimal_centavos_e_identidade(centavos: int) -> None:
    assert para_centavos(de_centavos(centavos)) == centavos


# Spec: STO-02
@settings(max_examples=200)
@given(st.decimals(min_value=Decimal("0.001"), max_value=Decimal("1e6"), places=3).filter(lambda d: d * 100 % 1 != 0))
def test_mais_de_duas_casas_sempre_rejeita(valor: Decimal) -> None:
    with pytest.raises(ValueError):
        para_centavos(valor)


# Spec: STO-08, STO-09, STO-10
@settings(max_examples=40)
@given(documentos_validos())
def test_importar_exportar_e_carregar_equivalem_ao_documento(doc: dict) -> None:
    doc = _sem_moeda(doc)
    motor, sessao, repo = _repo_novo()
    try:
        repo.importar_documento(doc)
        esperado = carregar_dados(doc)

        assert repo.carregar_livro() == esperado
        assert carregar_dados(repo.exportar_documento()) == esperado
    finally:
        sessao.close()
        motor.dispose()


# Spec: STO-12, STO-13
@settings(max_examples=40)
@given(documentos_validos(), st.data())
def test_apagar_tira_dos_totais_e_restaurar_devolve(doc: dict, dados) -> None:
    doc = _sem_moeda(doc)
    motor, sessao, repo = _repo_novo()
    try:
        repo.importar_documento(doc)
        original = repo.carregar_livro()
        todos = [(a, m, i) for (a, m) in repo.meses() for i in repo.listar_mes(a, m)]
        if not todos:
            return
        escolhidos = dados.draw(st.lists(st.sampled_from(todos), unique_by=lambda t: t[2].id, max_size=len(todos)))

        for _, _, item in escolhidos:
            repo.apagar_lancamento(item.id)

        livro = repo.carregar_livro()
        for numero_ano, ano in original.anos.items():
            for numero_mes, mes in ano.meses.items():
                apagados = [i for (a, m, i) in escolhidos if (a, m) == (numero_ano, numero_mes)]
                tirado = {t: sum((i.valor for i in apagados if i.tipo == t), Decimal(0)) for t in ("receita", "despesa", "investimento")}
                atual = livro.ano(numero_ano).mes(numero_mes)
                assert atual.total_receitas == mes.total_receitas - tirado["receita"]
                assert atual.total_despesas == mes.total_despesas - tirado["despesa"]
                assert atual.total_investimentos == mes.total_investimentos - tirado["investimento"]
        registros_csv = list(csv.reader(io.StringIO(exportar_csv_bytes(livro)[0].decode("utf-8"), newline="")))
        linhas_csv = len(registros_csv) - 1  # sem o cabeçalho; campos podem ter quebra de linha
        assert linhas_csv == sum(len(m.receitas) + len(m.despesas) + len(m.investimentos) for a in livro.anos.values() for m in a.meses.values())

        for _, _, item in escolhidos:
            repo.restaurar(item.id)
        assert repo.carregar_livro() == original
        assert repo.listar_lixeira() == []
    finally:
        sessao.close()
        motor.dispose()
