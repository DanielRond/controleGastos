"""Lançamentos, meses, painéis e dinheiro na API (WEB-05 a WEB-11, WEB-17)."""

import csv
import io
import zipfile
from decimal import Decimal
from pathlib import Path

import pytest

pytest.importorskip("fastapi")

from openpyxl import load_workbook

from controlegastos.loader import carregar_json
from controlegastos.resumo import (
    patrimonio_acumulado,
    ranking_despesas,
    variacao_saldo,
)

RAIZ = Path(__file__).resolve().parent.parent
EXEMPLO = RAIZ / "data" / "entradas" / "exemplo.json"
COMPLETO = RAIZ / "data" / "entradas" / "exemplo-completo.json"


def _lanc(**extra) -> dict:
    base = {"ano": 2025, "mes": 1, "tipo": "despesa", "descricao": "Mercado", "valor": "100.50", "dia": 3}
    return {**base, **extra}


def _importar(cliente, caminho: Path = EXEMPLO) -> None:
    resposta = cliente.post("/api/importar/json", content=caminho.read_bytes(), headers={"content-type": "application/json"})
    assert resposta.status_code == 200, resposta.text


# Spec: WEB-05, WEB-17
def test_criar_lancamento_devolve_201_com_dinheiro_em_texto(ana) -> None:
    resposta = ana.post("/api/lancamentos", json=_lanc(categoria="alimentacao"))

    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["valor"] == "100.50"
    assert isinstance(corpo["id"], int)
    assert {k: corpo[k] for k in ("ano", "mes", "tipo", "descricao", "dia", "categoria", "origem")} == {
        "ano": 2025, "mes": 1, "tipo": "despesa", "descricao": "Mercado", "dia": 3, "categoria": "alimentacao", "origem": "manual",
    }


# Spec: WEB-05
def test_investimento_aceita_tipo_e_ativo(ana) -> None:
    corpo = ana.post(
        "/api/lancamentos", json=_lanc(tipo="investimento", descricao="Aporte", tipo_investimento="fii", ativo="KNSC11")
    ).json()
    assert (corpo["tipo_investimento"], corpo["ativo"]) == ("fii", "KNSC11")


# Spec: WEB-05
def test_editar_e_apagar_lancamento(ana) -> None:
    id_ = ana.post("/api/lancamentos", json=_lanc()).json()["id"]

    editado = ana.patch(f"/api/lancamentos/{id_}", json={"descricao": "Feira", "valor": "90.00"})
    assert editado.status_code == 200
    assert (editado.json()["descricao"], editado.json()["valor"], editado.json()["dia"]) == ("Feira", "90.00", 3)

    assert ana.delete(f"/api/lancamentos/{id_}").status_code == 204
    assert ana.get("/api/meses/2025/1").json()["lancamentos"] == []
    assert ana.patch(f"/api/lancamentos/{id_}", json={"descricao": "x"}).status_code == 404  # na lixeira
    assert ana.delete(f"/api/lancamentos/{id_}").status_code == 404
    assert ana.patch("/api/lancamentos/99999", json={"descricao": "x"}).status_code == 404


# Spec: WEB-02, WEB-05
def test_lancamento_de_outro_usuario_responde_404_e_nao_vaza(ana, beto) -> None:
    id_ = ana.post("/api/lancamentos", json=_lanc()).json()["id"]

    assert beto.patch(f"/api/lancamentos/{id_}", json={"descricao": "invadido"}).status_code == 404
    assert beto.delete(f"/api/lancamentos/{id_}").status_code == 404
    assert beto.get("/api/meses/2025/1").json()["lancamentos"] == []
    assert beto.get("/api/exportar/json").json()["anos"] == []
    assert ana.get("/api/meses/2025/1").json()["lancamentos"][0]["descricao"] == "Mercado"


# Spec: WEB-06
def test_mes_lista_por_dia_e_id_com_totais_e_salario_como_receita(ana) -> None:
    ana.put("/api/meses/2025/1", json={"salario": "1000.00"})
    ana.post("/api/lancamentos", json=_lanc(descricao="B", dia=20, valor="50.00"))
    ana.post("/api/lancamentos", json=_lanc(descricao="A", dia=5, valor="30.25"))
    ana.post("/api/lancamentos", json=_lanc(tipo="receita", descricao="Freela", dia=5, valor="200.00"))
    ana.post("/api/lancamentos", json=_lanc(tipo="investimento", descricao="CDB", dia=9, valor="100.00", tipo_investimento="renda_fixa"))

    mes = ana.get("/api/meses/2025/1").json()

    assert [(item["dia"], item["descricao"]) for item in mes["lancamentos"]] == [(5, "A"), (5, "Freela"), (9, "CDB"), (20, "B")]
    assert mes["salario"] == "1000.00"
    assert mes["totais"] == {"receitas": "1200.00", "despesas": "80.25", "investimentos": "100.00", "saldo_livre": "1019.75"}


# Spec: WEB-06
def test_mes_sem_dados_responde_200_vazio(ana) -> None:
    resposta = ana.get("/api/meses/2031/7")
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["lancamentos"] == []
    assert corpo["salario"] is None
    assert corpo["totais"] == {"receitas": "0.00", "despesas": "0.00", "investimentos": "0.00", "saldo_livre": "0.00"}
    assert corpo["investimentos_por_classe"] == []
    assert corpo["meta"] is None


# Spec: WEB-07
def test_definir_salario_e_meta_parcialmente_e_limpar(ana) -> None:
    assert ana.put("/api/meses/2025/2", json={"salario": "3000.00", "meta_investimento": "500.00"}).status_code == 200
    ana.put("/api/meses/2025/2", json={"meta_investimento": "600.00"})  # salário não enviado: não muda
    mes = ana.get("/api/meses/2025/2").json()
    assert (mes["salario"], mes["meta_investimento"]) == ("3000.00", "600.00")

    ana.put("/api/meses/2025/2", json={"salario": None})
    mes = ana.get("/api/meses/2025/2").json()
    assert (mes["salario"], mes["meta_investimento"]) == (None, "600.00")


# Spec: WEB-08
def test_erros_de_validacao_vem_todos_de_uma_vez_e_nada_e_gravado(ana) -> None:
    resposta = ana.post("/api/lancamentos", json=_lanc(mes=2, dia=31, tipo="investimento", valor="1.00"))

    assert resposta.status_code == 422
    erros = resposta.json()["erros"]
    assert {e["caminho"] for e in erros} == {"dia", "tipo"}
    assert all(e["mensagem"] for e in erros)
    assert ana.get("/api/meses/2025/2").json()["lancamentos"] == []


# Spec: WEB-08
def test_campos_obrigatorios_e_tipos_errados_tambem_viram_erros_no_mesmo_formato(ana) -> None:
    resposta = ana.post("/api/lancamentos", json={"ano": 2025, "mes": "janeiro", "tipo": "despesa"})
    assert resposta.status_code == 422
    caminhos = {e["caminho"] for e in resposta.json()["erros"]}
    assert {"mes", "descricao", "valor", "dia"} <= caminhos

    resposta = ana.post("/api/lancamentos", json=_lanc(tipo="outro"))
    assert resposta.status_code == 422
    assert resposta.json()["erros"][0]["caminho"] == "tipo"


# Spec: WEB-08
def test_mais_de_duas_casas_e_erro_no_campo(ana) -> None:
    resposta = ana.post("/api/lancamentos", json=_lanc(valor="10.123"))
    assert resposta.status_code == 422
    assert resposta.json()["erros"] == [{"caminho": "valor", "mensagem": "valor deve ter no máximo 2 casas decimais"}]


# Spec: WEB-17
def test_dinheiro_na_entrada_so_aceita_texto_decimal(ana) -> None:
    for ruim in (100.5, 100, True, "abc", "1,5", "", None):
        resposta = ana.post("/api/lancamentos", json=_lanc(valor=ruim))
        assert resposta.status_code == 422, ruim
        assert resposta.json()["erros"][0]["caminho"] == "valor"
    assert ana.put("/api/meses/2025/1", json={"salario": 1000}).status_code == 422
    assert ana.post("/api/lancamentos", json=_lanc(valor="12.5")).json()["valor"] == "12.50"
    assert ana.post("/api/lancamentos", json=_lanc(valor="7")).json()["valor"] == "7.00"


# Spec: WEB-17
def test_todo_dinheiro_da_saida_e_texto_com_duas_casas(ana) -> None:
    _importar(ana)
    mes = ana.get("/api/meses/2025/1").json()
    ano = ana.get("/api/anos/2025/resumo").json()

    def dinheiro(x):
        assert isinstance(x, str)
        assert Decimal(x) == Decimal(x).quantize(Decimal("0.01"))
        assert len(x.split(".")[-1]) == 2

    for item in mes["lancamentos"]:
        dinheiro(item["valor"])
    for valor in mes["totais"].values():
        dinheiro(valor)
    for linha in ano["meses"]:
        for chave in ("receitas", "despesas", "investimentos", "saldo_livre"):
            dinheiro(linha[chave])
    for linha in ano["patrimonio"] + ano["variacao"]:
        dinheiro(linha["valor"])
    for linha in ano["ranking"]:
        dinheiro(linha["total"])


# Spec: WEB-09
def test_painel_do_mes_traz_classes_percentuais_e_meta_como_na_planilha(ana) -> None:
    _importar(ana, COMPLETO)
    mes = ana.get("/api/meses/2025/1").json()

    classes = {c["tipo"]: (c["total"], c["percentual"]) for c in mes["investimentos_por_classe"]}
    assert classes == {"cripto": ("111.37", "14.95"), "fii": ("187.67", "25.20"), "renda_fixa": ("445.74", "59.85")}
    assert mes["meta"] == {"valor": "850.00", "investido": "744.78", "diferenca": "105.22", "situacao": "falta"}


# Spec: WEB-09
def test_meta_ultrapassada_e_marcada_como_acima(ana) -> None:
    ana.put("/api/meses/2025/3", json={"meta_investimento": "50.00"})
    ana.post("/api/lancamentos", json=_lanc(mes=3, tipo="investimento", valor="80.00", tipo_investimento="cripto"))
    meta = ana.get("/api/meses/2025/3").json()["meta"]
    assert meta == {"valor": "50.00", "investido": "80.00", "diferenca": "-30.00", "situacao": "acima"}


# Spec: WEB-09
def test_valores_de_referencia_do_exemplo(ana) -> None:
    _importar(ana)
    mes = ana.get("/api/meses/2025/1").json()
    assert mes["totais"] == {"receitas": "5250.00", "despesas": "1780.00", "investimentos": "1000.00", "saldo_livre": "2470.00"}
    assert mes["meta"]["valor"] == "1000.00"
    assert mes["meta"]["diferenca"] == "0.00"


# Spec: WEB-10
def test_resumo_do_ano_usa_as_mesmas_funcoes_do_resumo(ana) -> None:
    _importar(ana, COMPLETO)
    livro = carregar_json(COMPLETO)
    ano = ana.get("/api/anos/2025/resumo").json()

    assert [(m["mes"], m["saldo_livre"]) for m in ano["meses"]] == [
        (n, f"{mes.saldo_livre:.2f}") for n, mes in sorted(livro.anos[2025].meses.items())
    ]
    assert [(p["rotulo"], p["valor"]) for p in ano["patrimonio"]] == [(r, f"{v:.2f}") for r, v in patrimonio_acumulado(livro)]
    assert [(r["categoria"], r["total"]) for r in ano["ranking"]] == [(c, f"{v:.2f}") for c, v in ranking_despesas(livro)]
    assert [(v["rotulo"], v["valor"]) for v in ano["variacao"]] == [(r, f"{v:.2f}") for r, v in variacao_saldo(livro)]


# Spec: WEB-10
def test_ano_sem_dados_responde_200_com_listas_vazias(ana) -> None:
    corpo = ana.get("/api/anos/1999/resumo").json()
    assert corpo == {"ano": 1999, "meses": [], "patrimonio": [], "ranking": [], "variacao": []}


# Spec: WEB-10
def test_ranking_agrupa_sem_categoria(ana) -> None:
    ana.post("/api/lancamentos", json=_lanc(categoria="geral", valor="10.00"))
    ana.post("/api/lancamentos", json=_lanc(categoria="", valor="5.00"))
    assert ana.get("/api/anos/2025/resumo").json()["ranking"] == [{"categoria": "Sem categoria", "total": "15.00"}]


# Spec: WEB-11
def test_api_csv_e_planilha_batem_com_os_numeros_do_painel(ana) -> None:
    _importar(ana, COMPLETO)
    resumo = ana.get("/api/anos/2025/resumo").json()["meses"]

    with zipfile.ZipFile(io.BytesIO(ana.get("/api/exportar/csv", params={"ano": 2025}).content)) as pacote:
        nome = next(n for n in pacote.namelist() if n.endswith("resumo-mensal.csv"))
        linhas = list(csv.DictReader(io.StringIO(pacote.read(nome).decode("utf-8"))))
    assert [(int(l["mes"]), l["saldo_livre"]) for l in linhas] == [(m["mes"], m["saldo_livre"]) for m in resumo]

    planilha = load_workbook(io.BytesIO(ana.get("/api/exportar/xlsx").content))["Resumo Geral"]
    saldos_planilha = [round(c.value, 2) for linha in planilha.iter_rows(min_row=2) for c in linha if isinstance(c.value, float)]
    for m in resumo:
        assert float(m["saldo_livre"]) in saldos_planilha
