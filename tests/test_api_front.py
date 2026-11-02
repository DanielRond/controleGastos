"""A API serve o front compilado na mesma origem (WEB-14, parte do modo local)."""

import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient

from controlegastos.web import Configuracao, criar_app


@pytest.fixture
def front(tmp_path):
    (tmp_path / "assets").mkdir()
    (tmp_path / "index.html").write_text("<html><body>INDEX</body></html>", encoding="utf-8")
    (tmp_path / "assets" / "app.js").write_text("console.log('ok')", encoding="utf-8")
    (tmp_path / "favicon.svg").write_text("<svg/>", encoding="utf-8")
    (tmp_path.parent / "segredo.txt").write_text("nao pode vazar", encoding="utf-8")
    config = Configuracao(database_url="sqlite://", chave_secreta="k" * 32)
    return TestClient(criar_app(config, pasta_front=tmp_path))


# Spec: WEB-14
def test_raiz_e_rotas_do_front_devolvem_o_index(front) -> None:
    for caminho in ("/", "/entrar", "/mes/2026/11", "/ano/2026", "/lixeira"):
        resposta = front.get(caminho)
        assert resposta.status_code == 200, caminho
        assert "INDEX" in resposta.text
        assert resposta.headers["content-type"].startswith("text/html")


# Spec: WEB-14
def test_arquivos_estaticos_sao_servidos(front) -> None:
    assert front.get("/assets/app.js").text == "console.log('ok')"
    assert front.get("/favicon.svg").text == "<svg/>"


# Spec: WEB-14
def test_rotas_da_api_continuam_sendo_da_api(front) -> None:
    desconhecida = front.get("/api/nao-existe")
    assert desconhecida.status_code == 404
    assert desconhecida.json() == {"detalhe": "Recurso não encontrado."}
    assert front.get("/api/me").status_code == 401
    assert front.get("/openapi.json").json()["info"]["title"] == "controleGastos"


# Spec: WEB-14
def test_nao_deixa_ler_arquivos_fora_da_pasta_do_front(front) -> None:
    for tentativa in ("/../segredo.txt", "/%2e%2e/segredo.txt", "/assets/../../segredo.txt", "/..%2fsegredo.txt"):
        resposta = front.get(tentativa)
        assert "nao pode vazar" not in resposta.text, tentativa


# Spec: WEB-14
def test_sem_front_compilado_a_raiz_nao_existe_mas_a_api_funciona(tmp_path) -> None:
    config = Configuracao(database_url="sqlite://", chave_secreta="k" * 32)
    cliente = TestClient(criar_app(config, pasta_front=tmp_path / "vazia"))

    assert cliente.get("/").status_code == 404
    assert cliente.get("/api/me").status_code == 401
