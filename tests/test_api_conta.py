"""Conta, sessão, CSRF e limite de tentativas (WEB-01 a WEB-04)."""

import pytest

pytest.importorskip("fastapi")

from controlegastos.web import Configuracao, criar_app
from controlegastos.web.seguranca import (
    assinar_sessao,
    gerar_hash,
    ler_sessao,
    verificar_hash,
)
from fastapi.testclient import TestClient

ROTAS_DE_DADOS = [
    ("GET", "/api/me"),
    ("GET", "/api/meses/2025/1"),
    ("PUT", "/api/meses/2025/1"),
    ("POST", "/api/lancamentos"),
    ("PATCH", "/api/lancamentos/1"),
    ("DELETE", "/api/lancamentos/1"),
    ("GET", "/api/anos/2025/resumo"),
    ("GET", "/api/exportar/xlsx"),
    ("GET", "/api/exportar/csv"),
    ("GET", "/api/exportar/json"),
    ("POST", "/api/importar/json"),
    ("GET", "/api/lixeira"),
    ("POST", "/api/lixeira/1/restaurar"),
    ("DELETE", "/api/lixeira/1"),
    ("DELETE", "/api/lixeira"),
]


# Spec: WEB-01
def test_login_devolve_usuario_e_csrf_e_grava_cookie_httponly_samesite(app, criar_conta) -> None:
    criar_conta("ana")
    resposta = TestClient(app).post("/api/auth/login", json={"nome": "ana", "senha": "senha-segura-123"})

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert set(corpo) == {"id", "nome", "csrf_token"}
    assert corpo["nome"] == "ana"
    cookie = resposta.headers["set-cookie"].lower()
    assert cookie.startswith("sessao=")
    assert "httponly" in cookie
    assert "samesite=lax" in cookie
    assert "max-age=604800" in cookie  # 7 dias
    assert "secure" not in cookie


# Spec: WEB-01
def test_senha_errada_e_usuario_inexistente_dao_a_mesma_resposta(app, criar_conta) -> None:
    criar_conta("ana")
    cliente = TestClient(app)
    errada = cliente.post("/api/auth/login", json={"nome": "ana", "senha": "senha-errada-123"})
    inexistente = cliente.post("/api/auth/login", json={"nome": "ninguem", "senha": "senha-segura-123"})

    assert errada.status_code == inexistente.status_code == 401
    assert errada.json() == inexistente.json()
    assert "set-cookie" not in errada.headers


# Spec: WEB-01
def test_me_e_logout(ana) -> None:
    assert ana.get("/api/me").json()["nome"] == "ana"
    assert ana.post("/api/auth/logout").status_code == 204
    assert ana.get("/api/me").status_code == 401


# Spec: WEB-01
def test_senha_e_guardada_com_argon2_e_nunca_em_texto(app, ana) -> None:
    import sqlalchemy as sa

    with app.state.motor.connect() as conexao:
        hash_guardado = conexao.execute(sa.text("select senha_hash from usuario where nome = 'ana'")).scalar_one()
    assert hash_guardado.startswith("$argon2")
    assert "senha-segura-123" not in hash_guardado
    assert verificar_hash("senha-segura-123", hash_guardado)
    assert not verificar_hash("outra", hash_guardado)
    assert gerar_hash("x" * 8) != gerar_hash("x" * 8)  # sal aleatório


# Spec: WEB-01
def test_nao_existe_cadastro_publico(app) -> None:
    cliente = TestClient(app)
    for caminho in ("/api/auth/registrar", "/api/auth/cadastro", "/api/usuarios"):
        assert cliente.post(caminho, json={"nome": "novo", "senha": "senha-segura-123"}).status_code in (404, 405)
    assert not [p for p in app.openapi()["paths"] if any(t in p for t in ("registr", "cadastr", "usuarios"))]


# Spec: WEB-01
def test_comando_usuario_criar_cria_a_conta_e_recusa_repeticao(tmp_path, monkeypatch, capsys) -> None:
    import getpass
    import sys

    from controlegastos.armazenamento import criar_engine, criar_sessao
    from controlegastos.cli import main

    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'c.db'}")
    respostas = iter(["senha-segura-123", "senha-segura-123"] * 3 + ["curta", "curta"] + ["senha-segura-123", "outra-senha-123"])
    monkeypatch.setattr(getpass, "getpass", lambda *_a, **_k: next(respostas))

    def rodar(*argumentos: str) -> int:
        monkeypatch.setattr(sys, "argv", ["controlegastos", *argumentos])
        return main()

    assert rodar("usuario", "criar", "ana") == 0
    assert "Usuário criado" in capsys.readouterr().out
    motor = criar_engine()
    from sqlalchemy import text

    with criar_sessao(motor) as sessao:
        hash_guardado = sessao.execute(text("select senha_hash from usuario where nome = 'ana'")).scalar_one()
    assert verificar_hash("senha-segura-123", hash_guardado)
    motor.dispose()

    assert rodar("usuario", "criar", "ana") == 1  # nome repetido
    assert rodar("usuario", "criar", "beto") == 0
    assert rodar("usuario", "criar", "carla") == 1  # senha com menos de 8 caracteres
    assert rodar("usuario", "criar", "dora") == 1  # confirmação diferente


# Spec: WEB-02
@pytest.mark.parametrize(("metodo", "caminho"), ROTAS_DE_DADOS)
def test_rotas_de_dados_exigem_sessao(app, metodo, caminho) -> None:
    resposta = TestClient(app).request(metodo, caminho, json={})
    assert resposta.status_code == 401
    assert "detalhe" in resposta.json()


# Spec: WEB-02
def test_cookie_adulterado_ou_expirado_e_recusado(app, ana) -> None:
    valido = ana.cookies.get("sessao")
    adulterado = TestClient(app, cookies={"sessao": valido + "x"})
    assert adulterado.get("/api/me").status_code == 401

    token = assinar_sessao({"usuario_id": 1, "csrf": "c"}, "chave-de-teste")
    assert ler_sessao(token, "chave-de-teste", max_age=10) == {"usuario_id": 1, "csrf": "c"}
    assert ler_sessao(token, "outra-chave", max_age=10) is None
    assert ler_sessao(token, "chave-de-teste", max_age=-1) is None  # expirado


# Spec: WEB-02
def test_usuario_apagado_nao_mantem_a_sessao(app, ana) -> None:
    import sqlalchemy as sa

    with app.state.motor.begin() as conexao:
        conexao.execute(sa.text("delete from usuario"))
    assert ana.get("/api/me").status_code == 401


# Spec: WEB-03
def test_escrita_exige_csrf_igual_ao_da_sessao(app, ana) -> None:
    sem = TestClient(app, cookies=ana.cookies)
    corpo = {"ano": 2025, "mes": 1, "tipo": "despesa", "descricao": "x", "valor": "1.00", "dia": 1}

    assert sem.post("/api/lancamentos", json=corpo).status_code == 403
    assert sem.post("/api/lancamentos", json=corpo, headers={"X-CSRF-Token": "errado"}).status_code == 403
    assert sem.get("/api/meses/2025/1").status_code == 200  # leitura não exige CSRF
    assert ana.post("/api/lancamentos", json=corpo).status_code == 201
    assert sem.delete("/api/lixeira").status_code == 403


# Spec: WEB-03
def test_cinco_falhas_bloqueiam_o_login_por_quinze_minutos(app, criar_conta) -> None:
    criar_conta("ana")
    relogio = {"t": 1000.0}
    app.state.limitador.relogio = lambda: relogio["t"]
    cliente = TestClient(app)

    for _ in range(5):
        assert cliente.post("/api/auth/login", json={"nome": "ana", "senha": "errada-errada"}).status_code == 401
    bloqueado = cliente.post("/api/auth/login", json={"nome": "ana", "senha": "senha-segura-123"})  # até a certa
    assert bloqueado.status_code == 429
    assert int(bloqueado.headers["retry-after"]) > 0
    assert "tentativas" in bloqueado.json()["detalhe"]

    relogio["t"] += 15 * 60 + 1
    assert cliente.post("/api/auth/login", json={"nome": "ana", "senha": "senha-segura-123"}).status_code == 200


# Spec: WEB-03
def test_login_com_sucesso_zera_o_contador_e_outro_nome_nao_e_afetado(app, criar_conta) -> None:
    criar_conta("ana")
    criar_conta("beto")
    cliente = TestClient(app)
    errada = {"nome": "ana", "senha": "errada-errada"}
    certa = {"nome": "ana", "senha": "senha-segura-123"}

    for _ in range(4):
        cliente.post("/api/auth/login", json=errada)
    assert cliente.post("/api/auth/login", json=certa).status_code == 200  # zera
    for _ in range(4):
        assert cliente.post("/api/auth/login", json=errada).status_code == 401  # ainda longe do limite

    for _ in range(5):
        cliente.post("/api/auth/login", json=errada)
    assert cliente.post("/api/auth/login", json={"nome": "beto", "senha": "senha-segura-123"}).status_code == 200


# Spec: WEB-04
def test_cookie_secure_so_quando_configurado() -> None:
    app = criar_app(Configuracao(database_url="sqlite://", chave_secreta="k" * 32, cookie_secure=True))
    from controlegastos.armazenamento import criar_sessao, criar_usuario

    with criar_sessao(app.state.motor) as sessao:
        criar_usuario(sessao, "ana", gerar_hash("senha-segura-123"))
    resposta = TestClient(app, base_url="https://testserver").post(
        "/api/auth/login", json={"nome": "ana", "senha": "senha-segura-123"}
    )
    assert "secure" in resposta.headers["set-cookie"].lower()


# Spec: WEB-04
def test_modo_hospedado_exige_chave_secreta_e_o_local_gera_uma(monkeypatch) -> None:
    with pytest.raises(RuntimeError, match="CHAVE_SECRETA"):
        criar_app(Configuracao(database_url="sqlite://", chave_secreta=None, cookie_secure=True))

    app = criar_app(Configuracao(database_url="sqlite://", chave_secreta=None, cookie_secure=False))
    assert len(app.state.config.chave_secreta) >= 32

    monkeypatch.setenv("CONTROLEGASTOS_COOKIE_SECURE", "1")
    monkeypatch.setenv("CONTROLEGASTOS_CHAVE_SECRETA", "abc")
    config = Configuracao.do_ambiente()
    assert config.cookie_secure is True
    assert config.chave_secreta == "abc"
