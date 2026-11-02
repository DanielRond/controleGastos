"""Arquivos, importação, lixeira e contrato OpenAPI da API (WEB-12, WEB-13, WEB-16, WEB-19)."""

import io
import json
import zipfile
from pathlib import Path

import pytest

pytest.importorskip("fastapi")

from openpyxl import load_workbook

from controlegastos.loader import carregar_dados, carregar_json

RAIZ = Path(__file__).resolve().parent.parent
EXEMPLO = RAIZ / "data" / "entradas" / "exemplo.json"
COMPLETO = RAIZ / "data" / "entradas" / "exemplo-completo.json"
JSON = {"content-type": "application/json"}


def _importar(cliente, caminho: Path = EXEMPLO, **params):
    return cliente.post("/api/importar/json", content=caminho.read_bytes(), headers=JSON, params=params)


def _lanc(**extra) -> dict:
    return {"ano": 2025, "mes": 1, "tipo": "despesa", "descricao": "Mercado", "valor": "100.50", "dia": 3, **extra}


# Spec: WEB-12
def test_exportar_xlsx_devolve_a_planilha_com_nome_de_arquivo(ana) -> None:
    _importar(ana)
    resposta = ana.get("/api/exportar/xlsx")

    assert resposta.status_code == 200
    assert resposta.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert 'filename="' in resposta.headers["content-disposition"]
    assert ".xlsx" in resposta.headers["content-disposition"]
    assert load_workbook(io.BytesIO(resposta.content)).sheetnames == ["Resumo Geral", "2025-01", "2025-02", "Gráficos"]


# Spec: WEB-12
def test_exportar_csv_devolve_zip_com_os_dois_arquivos(ana) -> None:
    _importar(ana)
    resposta = ana.get("/api/exportar/csv")

    assert resposta.headers["content-type"] == "application/zip"
    assert ".zip" in resposta.headers["content-disposition"]
    with zipfile.ZipFile(io.BytesIO(resposta.content)) as pacote:
        nomes = sorted(pacote.namelist())
        assert len(nomes) == 2
        cabecalhos = {n: pacote.read(n).decode("utf-8").splitlines()[0] for n in nomes}
    assert "data,tipo,descricao,categoria,ativo,valor" in cabecalhos.values()
    assert "ano,mes,receitas,despesas,investimentos,saldo_livre" in cabecalhos.values()


# Spec: WEB-12
def test_filtro_por_ano_limita_os_arquivos(ana) -> None:
    _importar(ana, COMPLETO)
    todos = load_workbook(io.BytesIO(ana.get("/api/exportar/xlsx").content)).sheetnames
    so_2026 = load_workbook(io.BytesIO(ana.get("/api/exportar/xlsx", params={"ano": 2026}).content)).sheetnames

    assert any(n.startswith("2025-") for n in todos)
    assert so_2026 != todos
    assert all(not n.startswith("2025-") for n in so_2026)
    assert any(n.startswith("2026-") for n in so_2026)


# Spec: WEB-12, WEB-19
def test_arquivos_nunca_trazem_itens_da_lixeira(ana) -> None:
    id_ = ana.post("/api/lancamentos", json=_lanc(descricao="SecretoApagado")).json()["id"]
    ana.post("/api/lancamentos", json=_lanc(descricao="Visivel"))
    ana.delete(f"/api/lancamentos/{id_}")

    with zipfile.ZipFile(io.BytesIO(ana.get("/api/exportar/csv").content)) as pacote:
        texto = "".join(pacote.read(n).decode("utf-8") for n in pacote.namelist())
    assert "Visivel" in texto
    assert "SecretoApagado" not in texto
    assert "SecretoApagado" not in json.dumps(ana.get("/api/exportar/json").json())


# Spec: WEB-13
def test_importar_informa_o_que_criou(ana) -> None:
    resposta = _importar(ana)

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["meses"] == [{"ano": 2025, "mes": 1}, {"ano": 2025, "mes": 2}]
    assert corpo["lancamentos_criados"] == sum(
        len(m.get(k, [])) for a in json.loads(EXEMPLO.read_text())["anos"] for m in a["meses"] for k in ("receitas", "despesas", "investimentos")
    )
    assert corpo["substituidos"] == 0


# Spec: WEB-13
def test_importar_invalido_da_422_com_todos_os_erros_e_nao_grava(ana) -> None:
    doc = json.loads(EXEMPLO.read_text())
    doc["anos"][0]["meses"][0]["despesas"][0]["dia"] = 40
    doc["anos"][0]["meses"][1]["mes"] = 13

    resposta = ana.post("/api/importar/json", json=doc)

    assert resposta.status_code == 422
    assert len(resposta.json()["erros"]) == 2
    assert all(e["caminho"].startswith("anos[0]") for e in resposta.json()["erros"])
    assert ana.get("/api/exportar/json").json()["anos"] == []


# Spec: WEB-13
def test_importar_json_ilegivel_da_422(ana) -> None:
    resposta = ana.post("/api/importar/json", content=b"{nao e json", headers=JSON)
    assert resposta.status_code == 422
    assert "JSON" in resposta.json()["erros"][0]["mensagem"]


# Spec: WEB-13
def test_importar_mes_existente_da_409_e_substituir_troca(ana) -> None:
    _importar(ana)
    antes = ana.get("/api/exportar/json").json()

    conflito = _importar(ana)
    assert conflito.status_code == 409
    assert conflito.json()["meses"] == [{"ano": 2025, "mes": 1}, {"ano": 2025, "mes": 2}]
    assert ana.get("/api/exportar/json").json() == antes

    novo = {"anos": [{"ano": 2025, "meses": [{"mes": 1, "despesas": [{"descricao": "Só esta", "valor": 1.5, "dia": 2}]}]}]}
    trocado = ana.post("/api/importar/json", json=novo, params={"substituir": "true"})
    assert trocado.status_code == 200
    assert trocado.json()["substituidos"] > 0
    assert [i["descricao"] for i in ana.get("/api/meses/2025/1").json()["lancamentos"]] == ["Só esta"]
    assert len(ana.get("/api/lixeira").json()) == trocado.json()["substituidos"]


# Spec: WEB-13
def test_exportar_json_faz_ida_e_volta(ana) -> None:
    _importar(ana, COMPLETO)
    exportado = ana.get("/api/exportar/json").json()
    assert carregar_dados(exportado) == carregar_json(COMPLETO)


# Spec: WEB-19
def test_lixeira_lista_restaura_exclui_e_esvazia(ana) -> None:
    ids = [ana.post("/api/lancamentos", json=_lanc(descricao=f"L{i}")).json()["id"] for i in range(3)]
    for id_ in ids:
        ana.delete(f"/api/lancamentos/{id_}")

    lixo = ana.get("/api/lixeira").json()
    assert sorted(i["id"] for i in lixo) == sorted(ids)
    assert all(i["apagado_em"] for i in lixo)
    assert ana.get("/api/meses/2025/1").json()["totais"]["despesas"] == "0.00"

    assert ana.post(f"/api/lixeira/{ids[0]}/restaurar").status_code == 200
    assert ana.get("/api/meses/2025/1").json()["totais"]["despesas"] == "100.50"
    assert ana.post(f"/api/lixeira/{ids[0]}/restaurar").status_code == 404  # já restaurado

    assert ana.delete(f"/api/lixeira/{ids[1]}").status_code == 204
    assert ana.delete(f"/api/lixeira/{ids[0]}").status_code == 404  # ativo não é excluído por aqui
    assert ana.delete("/api/lixeira").json() == {"removidos": 1}
    assert ana.get("/api/lixeira").json() == []


# Spec: WEB-19, WEB-02
def test_lixeira_e_isolada_por_usuario(ana, beto) -> None:
    id_ = ana.post("/api/lancamentos", json=_lanc()).json()["id"]
    ana.delete(f"/api/lancamentos/{id_}")

    assert beto.get("/api/lixeira").json() == []
    assert beto.post(f"/api/lixeira/{id_}/restaurar").status_code == 404
    assert beto.delete(f"/api/lixeira/{id_}").status_code == 404
    assert beto.delete("/api/lixeira").json() == {"removidos": 0}
    assert len(ana.get("/api/lixeira").json()) == 1


# Spec: WEB-16
def test_openapi_documenta_as_rotas_e_o_instantaneo_versionado_esta_em_dia(app) -> None:
    esquema = app.openapi()
    caminhos = set(esquema["paths"])
    assert {
        "/api/auth/login", "/api/auth/logout", "/api/me", "/api/meses/{ano}/{mes}", "/api/lancamentos",
        "/api/lancamentos/{id}", "/api/anos/{ano}/resumo", "/api/exportar/{formato}", "/api/importar/json",
        "/api/lixeira", "/api/lixeira/{id}", "/api/lixeira/{id}/restaurar",
    } <= caminhos

    instantaneo = json.loads((RAIZ / "specs" / "api" / "openapi.json").read_text(encoding="utf-8"))
    assert instantaneo == esquema, "rode: uv run python scripts/exportar_openapi.py"
