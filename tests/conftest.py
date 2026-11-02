"""Configuração compartilhada dos testes.

Perfil do Hypothesis: o gerador de documentos é composto e a verificação
`too_slow` oscila conforme a carga da máquina (falhou 1 em 25 execuções,
sem relação com a lógica). Sem prazo por exemplo e sem essa verificação,
as propriedades ficam determinísticas quanto a tempo.
"""

from hypothesis import HealthCheck, settings

settings.register_profile(
    "controlegastos",
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
settings.load_profile("controlegastos")


# --- Fixtures do armazenamento (exigem o extra `web`) --------------------------------------
import pytest


@pytest.fixture
def engine():
    """Banco SQLite em memória, já migrado pelo Alembic (as migrações fazem parte do teste)."""
    pytest.importorskip("sqlalchemy")
    from controlegastos.armazenamento import aplicar_migracoes, criar_engine

    motor = criar_engine("sqlite://")
    aplicar_migracoes(motor)
    yield motor
    motor.dispose()


@pytest.fixture
def sessao(engine):
    from controlegastos.armazenamento import criar_sessao

    with criar_sessao(engine) as s:
        yield s


@pytest.fixture
def repo(sessao):
    from controlegastos.armazenamento import Repositorio, criar_usuario

    return Repositorio(sessao, criar_usuario(sessao, "ana", "hash-ana"))


@pytest.fixture
def repo_outro(sessao):
    from controlegastos.armazenamento import Repositorio, criar_usuario

    return Repositorio(sessao, criar_usuario(sessao, "beto", "hash-beto"))


# --- Fixtures da API (exigem o extra `web`) -------------------------------------------------
SENHA_PADRAO = "senha-segura-123"


@pytest.fixture
def app():
    pytest.importorskip("fastapi")
    from controlegastos.web import Configuracao, criar_app

    return criar_app(Configuracao(database_url="sqlite://", chave_secreta="chave-de-teste", cookie_secure=False))


@pytest.fixture
def criar_conta(app):
    def _criar(nome: str, senha: str = SENHA_PADRAO) -> int:
        from controlegastos.armazenamento import criar_sessao, criar_usuario
        from controlegastos.web.seguranca import gerar_hash

        with criar_sessao(app.state.motor) as sessao:
            return criar_usuario(sessao, nome, gerar_hash(senha))

    return _criar


@pytest.fixture
def entrar(app, criar_conta):
    """Devolve uma função que cria a conta (se preciso), faz login e devolve o cliente já com o CSRF."""
    from fastapi.testclient import TestClient

    contas: set[str] = set()

    def _entrar(nome: str = "ana", senha: str = SENHA_PADRAO) -> TestClient:
        if nome not in contas:
            criar_conta(nome, senha)
            contas.add(nome)
        cliente = TestClient(app)
        resposta = cliente.post("/api/auth/login", json={"nome": nome, "senha": senha})
        assert resposta.status_code == 200, resposta.text
        cliente.headers["X-CSRF-Token"] = resposta.json()["csrf_token"]
        return cliente

    return _entrar


@pytest.fixture
def ana(entrar):
    return entrar("ana")


@pytest.fixture
def beto(entrar):
    return entrar("beto")
