import copy
import json
from pathlib import Path

import pytest

from controlegastos.validador import (
    TIPOS_DE_INVESTIMENTO_CONHECIDOS,
    ErroDeValidacao,
    validar,
)

RAIZ_PROJETO = Path(__file__).resolve().parent.parent


def _doc_valido() -> dict:
    return {
        "moeda": "BRL",
        "anos": [
            {
                "ano": 2025,
                "meses": [
                    {
                        "mes": 1,
                        "salario": 5000,
                        "meta_investimento": 250.5,
                        "receitas": [{"descricao": "Extra", "valor": 10.0, "dia": 3}],
                        "despesas": [
                            {"descricao": "Aluguel", "valor": 1000, "dia": 5, "categoria": "x"}
                        ],
                        "investimentos": [
                            {
                                "tipo": "fii",
                                "ativo": "KNSC11",
                                "descricao": "Compra",
                                "valor": 100.0,
                                "dia": 10,
                            }
                        ],
                    }
                ],
            }
        ],
    }


def _caminhos(dados: object) -> list[str]:
    return [e.caminho for e in validar(dados)]


def _mes(doc: dict) -> dict:
    return doc["anos"][0]["meses"][0]


def test_documento_valido_sem_erros():
    assert validar(_doc_valido()) == []


def test_str_do_erro():
    assert str(ErroDeValidacao("a.b", "msg")) == "a.b: msg"


def test_tipos_conhecidos():
    assert TIPOS_DE_INVESTIMENTO_CONHECIDOS == {"renda_fixa", "fii", "cripto"}


@pytest.mark.parametrize("raiz", [[], "texto", 1, None])
def test_raiz_nao_objeto(raiz):
    erros = validar(raiz)
    assert len(erros) == 1
    assert erros[0].caminho == "(raiz)"


def test_anos_ausente():
    assert _caminhos({}) == ["anos"]


def test_anos_nao_lista():
    assert _caminhos({"anos": {}}) == ["anos"]


def test_ano_ausente_e_meses_ausente():
    assert _caminhos({"anos": [{}]}) == ["anos[0].ano", "anos[0].meses"]


@pytest.mark.parametrize("ano", ["2025", True, 0, 10000, 2025.0])
def test_ano_invalido(ano):
    doc = _doc_valido()
    doc["anos"][0]["ano"] = ano
    assert _caminhos(doc) == ["anos[0].ano"]


def test_meses_nao_lista():
    doc = _doc_valido()
    doc["anos"][0]["meses"] = "x"
    assert _caminhos(doc) == ["anos[0].meses"]


@pytest.mark.parametrize("mes", [0, 13, True, "1", 1.5])
def test_mes_invalido_sem_cascata(mes):
    doc = _doc_valido()
    _mes(doc)["mes"] = mes
    # Dia não é validado quando o mês é inválido.
    assert _caminhos(doc) == ["anos[0].meses[0].mes"]


def test_mes_ausente():
    doc = _doc_valido()
    del _mes(doc)["mes"]
    assert _caminhos(doc) == ["anos[0].meses[0].mes"]


def test_dia_29_fevereiro_bissexto_valido():
    doc = _doc_valido()
    doc["anos"][0]["ano"] = 2024
    _mes(doc)["mes"] = 2
    _mes(doc)["despesas"][0]["dia"] = 29
    assert validar(doc) == []


def test_dia_29_fevereiro_nao_bissexto_invalido():
    doc = _doc_valido()
    doc["anos"][0]["ano"] = 2025
    _mes(doc)["mes"] = 2
    _mes(doc)["despesas"][0]["dia"] = 29
    assert _caminhos(doc) == ["anos[0].meses[0].despesas[0].dia"]


@pytest.mark.parametrize("dia", [0, 32, -1, True, "5", 5.0])
def test_dia_invalido(dia):
    doc = _doc_valido()
    _mes(doc)["receitas"][0]["dia"] = dia
    assert _caminhos(doc) == ["anos[0].meses[0].receitas[0].dia"]


def test_dia_31_em_mes_de_30_dias():
    doc = _doc_valido()
    _mes(doc)["mes"] = 4
    _mes(doc)["despesas"][0]["dia"] = 31
    assert _caminhos(doc) == ["anos[0].meses[0].despesas[0].dia"]


@pytest.mark.parametrize("valor", [True, False, "10.5", None, float("inf"), float("nan"), []])
def test_valor_invalido(valor):
    doc = _doc_valido()
    _mes(doc)["despesas"][0]["valor"] = valor
    assert _caminhos(doc) == ["anos[0].meses[0].despesas[0].valor"]


def test_valor_booleano_mensagem_em_portugues():
    doc = _doc_valido()
    _mes(doc)["despesas"][0]["valor"] = True
    (erro,) = validar(doc)
    assert "numérico" in erro.mensagem


@pytest.mark.parametrize("campo", ["salario", "meta_investimento"])
@pytest.mark.parametrize("valor", [True, "100", float("inf")])
def test_campos_monetarios_do_mes_invalidos(campo, valor):
    doc = _doc_valido()
    _mes(doc)[campo] = valor
    assert _caminhos(doc) == [f"anos[0].meses[0].{campo}"]


def test_campos_monetarios_opcionais_ausentes():
    doc = _doc_valido()
    del _mes(doc)["salario"]
    del _mes(doc)["meta_investimento"]
    assert validar(doc) == []


@pytest.mark.parametrize("campo", ["receitas", "despesas", "investimentos"])
def test_lista_de_lancamentos_nao_lista(campo):
    doc = _doc_valido()
    _mes(doc)[campo] = {}
    assert _caminhos(doc) == [f"anos[0].meses[0].{campo}"]


def test_lancamento_nao_objeto():
    doc = _doc_valido()
    _mes(doc)["despesas"].append(5)
    assert _caminhos(doc) == ["anos[0].meses[0].despesas[1]"]


@pytest.mark.parametrize("campo", ["descricao", "valor", "dia"])
@pytest.mark.parametrize("lista", ["receitas", "despesas", "investimentos"])
def test_campo_obrigatorio_ausente(lista, campo):
    doc = _doc_valido()
    del _mes(doc)[lista][0][campo]
    assert _caminhos(doc) == [f"anos[0].meses[0].{lista}[0].{campo}"]


def test_tipo_ausente_em_investimento():
    doc = _doc_valido()
    del _mes(doc)["investimentos"][0]["tipo"]
    assert _caminhos(doc) == ["anos[0].meses[0].investimentos[0].tipo"]


@pytest.mark.parametrize("tipo", ["acoes", "fiis", 3, None])
def test_tipo_desconhecido(tipo):
    doc = _doc_valido()
    _mes(doc)["investimentos"][0]["tipo"] = tipo
    assert _caminhos(doc) == ["anos[0].meses[0].investimentos[0].tipo"]


@pytest.mark.parametrize("tipo", sorted(TIPOS_DE_INVESTIMENTO_CONHECIDOS))
def test_tipo_conhecido_valido(tipo):
    doc = _doc_valido()
    _mes(doc)["investimentos"][0]["tipo"] = tipo
    assert validar(doc) == []


def test_textos_opcionais_invalidos():
    doc = _doc_valido()
    doc["moeda"] = 1
    _mes(doc)["despesas"][0]["categoria"] = 2
    _mes(doc)["investimentos"][0]["ativo"] = 3
    assert sorted(_caminhos(doc)) == sorted(
        [
            "moeda",
            "anos[0].meses[0].despesas[0].categoria",
            "anos[0].meses[0].investimentos[0].ativo",
        ]
    )


def test_descricao_nao_texto():
    doc = _doc_valido()
    _mes(doc)["receitas"][0]["descricao"] = 1
    assert _caminhos(doc) == ["anos[0].meses[0].receitas[0].descricao"]


def test_todos_os_erros_de_uma_vez():
    doc = _doc_valido()
    _mes(doc)["salario"] = True
    _mes(doc)["despesas"][0]["valor"] = "x"
    _mes(doc)["investimentos"][0]["tipo"] = "zzz"
    assert len(validar(doc)) == 3


def test_nao_muta_entrada():
    doc = _doc_valido()
    copia = copy.deepcopy(doc)
    validar(doc)
    assert doc == copia


@pytest.mark.parametrize("nome", ["exemplo.json", "exemplo-completo.json"])
def test_arquivos_de_exemplo_validos(nome):
    caminho = RAIZ_PROJETO / "data" / "entradas" / nome
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    assert validar(dados) == []
