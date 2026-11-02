"""Comando `controlegastos web` e a rota de saúde (WEB-14, WEB-28)."""

import io
import logging
import sys

import pytest

pytest.importorskip("fastapi")

import sqlalchemy as sa
from fastapi.testclient import TestClient

from controlegastos.cli import main


@pytest.fixture
def uvicorn_falso(monkeypatch, tmp_path):
    """Troca o uvicorn por um dublê que só registra como foi chamado, e isola o banco em tmp_path."""
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("CONTROLEGASTOS_COOKIE_SECURE", raising=False)
    monkeypatch.delenv("CONTROLEGASTOS_CHAVE_SECRETA", raising=False)
    monkeypatch.setenv("CONTROLEGASTOS_DADOS", str(tmp_path / "dados"))
    chamadas: dict = {}
    monkeypatch.setattr("uvicorn.run", lambda app, **opcoes: chamadas.update(app=app, **opcoes))
    return chamadas


def rodar(monkeypatch, *argumentos: str) -> int:
    monkeypatch.setattr(sys, "argv", ["controlegastos", *argumentos])
    return main()


# Spec: WEB-14
def test_por_padrao_liga_so_a_maquina_local_na_porta_8000_e_diz_o_endereco(monkeypatch, uvicorn_falso, capsys) -> None:
    assert rodar(monkeypatch, "web") == 0

    assert (uvicorn_falso["host"], uvicorn_falso["port"]) == ("127.0.0.1", 8000)
    assert "http://127.0.0.1:8000" in capsys.readouterr().out


# Spec: WEB-14
def test_o_app_entregue_ao_servidor_continua_exigindo_login(monkeypatch, uvicorn_falso) -> None:
    rodar(monkeypatch, "web")
    cliente = TestClient(uvicorn_falso["app"])

    assert cliente.get("/api/me").status_code == 401
    assert cliente.get("/api/meses/2026/11").status_code == 401


# Spec: WEB-14
def test_porta_e_host_podem_ser_escolhidos(monkeypatch, uvicorn_falso, capsys) -> None:
    rodar(monkeypatch, "web", "--porta", "9123", "--host", "localhost")

    assert (uvicorn_falso["host"], uvicorn_falso["port"]) == ("localhost", 9123)
    assert "http://localhost:9123" in capsys.readouterr().out


# Spec: WEB-14
def test_cria_o_sqlite_local_e_aplica_as_migracoes_ao_iniciar(monkeypatch, uvicorn_falso, tmp_path) -> None:
    rodar(monkeypatch, "web")

    banco = tmp_path / "dados" / "controlegastos.db"
    assert banco.exists()
    motor = sa.create_engine(f"sqlite:///{banco}")
    assert {"usuario", "mes", "lancamento"} <= set(sa.inspect(motor).get_table_names())
    motor.dispose()


# Spec: WEB-14
def test_endereco_fora_da_maquina_sem_https_gera_aviso(monkeypatch, uvicorn_falso, caplog) -> None:
    with caplog.at_level(logging.WARNING):
        rodar(monkeypatch, "web", "--host", "0.0.0.0")
    assert "HTTPS" in caplog.text
    assert "CONTROLEGASTOS_COOKIE_SECURE" in caplog.text


# Spec: WEB-14
@pytest.mark.parametrize("host", ["127.0.0.1", "localhost", "::1"])
def test_loopback_nao_gera_aviso(monkeypatch, uvicorn_falso, caplog, host) -> None:
    with caplog.at_level(logging.WARNING):
        rodar(monkeypatch, "web", "--host", host)
    assert "HTTPS" not in caplog.text


# Spec: WEB-14
def test_fora_da_maquina_com_https_configurado_nao_gera_aviso(monkeypatch, uvicorn_falso, caplog) -> None:
    monkeypatch.setenv("CONTROLEGASTOS_COOKIE_SECURE", "1")
    monkeypatch.setenv("CONTROLEGASTOS_CHAVE_SECRETA", "k" * 40)
    with caplog.at_level(logging.WARNING):
        assert rodar(monkeypatch, "web", "--host", "0.0.0.0") == 0
    assert "HTTPS" not in caplog.text


# Spec: WEB-14
def test_sem_o_front_compilado_avisa_e_serve_so_a_api(monkeypatch, uvicorn_falso, caplog, tmp_path) -> None:
    monkeypatch.setattr("controlegastos.web.app.PASTA_DO_FRONT", tmp_path / "sem-front")
    with caplog.at_level(logging.WARNING):
        assert rodar(monkeypatch, "web") == 0

    assert "Front-end não compilado" in caplog.text
    assert "npm run build" in caplog.text
    cliente = TestClient(uvicorn_falso["app"])
    assert cliente.get("/").status_code == 404
    assert cliente.get("/api/saude").status_code == 200


# Spec: WEB-14, WEB-04
def test_modo_https_sem_chave_secreta_para_com_mensagem_clara(monkeypatch, uvicorn_falso, caplog) -> None:
    monkeypatch.setenv("CONTROLEGASTOS_COOKIE_SECURE", "1")
    with caplog.at_level(logging.ERROR):
        assert rodar(monkeypatch, "web") == 1
    assert "CONTROLEGASTOS_CHAVE_SECRETA" in caplog.text
    assert "app" not in uvicorn_falso  # nem tentou subir


# Spec: WEB-28
def test_saude_responde_ok_sem_login_e_sem_cookie(app) -> None:
    resposta = TestClient(app).get("/api/saude")

    assert resposta.status_code == 200
    assert resposta.json() == {"status": "ok"}
    assert "set-cookie" not in resposta.headers


# Spec: WEB-28
def test_saude_responde_503_quando_o_banco_nao_responde(app, monkeypatch) -> None:
    def quebrado(*_a, **_k):
        raise sa.exc.OperationalError("select 1", {}, Exception("banco fora do ar"))

    monkeypatch.setattr(app.state.motor, "connect", quebrado)
    resposta = TestClient(app).get("/api/saude")

    assert resposta.status_code == 503
    assert "banco" in resposta.json()["detalhe"].lower()


# Spec: WEB-01
def test_usuario_criar_le_a_senha_da_entrada_padrao(monkeypatch, tmp_path, capsys) -> None:
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'c.db'}")
    monkeypatch.setattr(sys, "stdin", io.StringIO("senha-segura-123\n"))

    assert rodar(monkeypatch, "usuario", "criar", "ana", "--senha-stdin") == 0
    assert "Usuário criado: ana" in capsys.readouterr().out

    from controlegastos.armazenamento import criar_engine
    from controlegastos.web.seguranca import verificar_hash

    motor = criar_engine()
    with motor.connect() as conexao:
        guardado = conexao.execute(sa.text("select senha_hash from usuario where nome = 'ana'")).scalar_one()
    motor.dispose()
    assert verificar_hash("senha-segura-123", guardado)


# Spec: WEB-01
@pytest.mark.parametrize("entrada", ["curta\n", "", "\n"])
def test_usuario_criar_por_stdin_recusa_senha_curta_ou_vazia(monkeypatch, tmp_path, entrada) -> None:
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'c.db'}")
    monkeypatch.setattr(sys, "stdin", io.StringIO(entrada))
    assert rodar(monkeypatch, "usuario", "criar", "ana", "--senha-stdin") == 1
