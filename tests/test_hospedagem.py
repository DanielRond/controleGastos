"""Artefatos do modo hospedado: Dockerfile, compose, .dockerignore e documentação (WEB-15)."""

import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
DOCKERFILE = (RAIZ / "Dockerfile").read_text(encoding="utf-8") if (RAIZ / "Dockerfile").exists() else ""
COMPOSE = (RAIZ / "docker-compose.yml").read_text(encoding="utf-8") if (RAIZ / "docker-compose.yml").exists() else ""


def _instrucoes(texto: str) -> list[str]:
    """Instruções do Dockerfile sem comentários, juntando as linhas continuadas com barra."""
    limpo = re.sub(r"\\\n", " ", texto)
    return [linha.strip() for linha in limpo.splitlines() if linha.strip() and not linha.strip().startswith("#")]


# Spec: WEB-15
def test_dockerfile_tem_dois_estagios_node_compila_e_python_roda() -> None:
    instrucoes = _instrucoes(DOCKERFILE)
    froms = [i for i in instrucoes if i.upper().startswith("FROM ")]

    assert len(froms) == 2
    assert "node:24" in froms[0]
    assert "python:3.14" in froms[1]
    assert any("npm run build" in i for i in instrucoes)
    assert any(i.startswith("COPY --from=") for i in instrucoes)
    assert any("--no-dev" in i and "--extra web" in i for i in instrucoes)


# Spec: WEB-15
def test_dockerfile_nao_roda_como_root_e_guarda_os_dados_em_volume() -> None:
    instrucoes = _instrucoes(DOCKERFILE)
    usuarios = [i.split(maxsplit=1)[1] for i in instrucoes if i.upper().startswith("USER ")]

    assert usuarios
    assert usuarios[-1].lower() not in ("root", "0")
    assert any(i.upper().startswith("VOLUME") and "/data" in i for i in instrucoes)
    assert any(i.startswith("ENV") and "CONTROLEGASTOS_DADOS=/data" in i for i in instrucoes)


# Spec: WEB-15
def test_dockerfile_sobe_o_app_em_todas_as_interfaces_e_verifica_a_saude() -> None:
    instrucoes = _instrucoes(DOCKERFILE)

    assert any(i.upper().startswith("CMD") and "controlegastos" in i and "web" in i and "0.0.0.0" in i for i in instrucoes)
    assert any(i.upper().startswith("HEALTHCHECK") and "/api/saude" in i for i in instrucoes)
    assert any(i.upper().startswith("EXPOSE") and "8000" in i for i in instrucoes)


# Spec: WEB-15
def test_nenhum_segredo_fixo_no_dockerfile_nem_no_compose() -> None:
    for nome, texto in (("Dockerfile", DOCKERFILE), ("docker-compose.yml", COMPOSE)):
        for linha in texto.splitlines():
            if linha.strip().startswith("#"):
                continue
            achado = re.search(r"(CHAVE_SECRETA|SECRET|SENHA|PASSWORD)\w*\s*[=:]\s*(\S+)", linha, re.IGNORECASE)
            if achado:
                valor = achado.group(2).strip("\"'")
                assert valor.startswith("${") or valor == "", f"{nome}: segredo fixo em: {linha.strip()}"


# Spec: WEB-15
def test_compose_exige_a_chave_secreta_usa_volume_e_configura_so_por_ambiente() -> None:
    assert "${CONTROLEGASTOS_CHAVE_SECRETA:?" in COMPOSE
    assert "CONTROLEGASTOS_COOKIE_SECURE" in COMPOSE
    assert re.search(r"/data", COMPOSE)
    assert "healthcheck" in COMPOSE
    assert "8000" in COMPOSE


# Spec: WEB-15
def test_dockerignore_deixa_dados_banco_e_dependencias_fora_da_imagem() -> None:
    linhas = {linha.strip() for linha in (RAIZ / ".dockerignore").read_text(encoding="utf-8").splitlines()}
    for esperado in ("dados/", "*.db", "frontend/node_modules/", ".git/", ".venv/", "data/entradas/20*.json"):
        assert esperado in linhas, esperado


# Spec: WEB-15
def test_documentacao_de_hospedagem_cobre_o_essencial() -> None:
    texto = (RAIZ / "docs" / "hospedagem.md").read_text(encoding="utf-8")
    for trecho in ("HTTPS", "usuario criar", "--senha-stdin", "backup", "/data", "CONTROLEGASTOS_CHAVE_SECRETA", "docker compose"):
        assert trecho.lower() in texto.lower(), trecho


# Spec: WEB-15
def test_a_configuracao_vem_so_de_variaveis_de_ambiente(monkeypatch, tmp_path) -> None:
    pytest.importorskip("fastapi")
    from controlegastos.web import criar_app

    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'fora' / 'x.db'}")
    monkeypatch.setenv("CONTROLEGASTOS_CHAVE_SECRETA", "k" * 40)
    monkeypatch.setenv("CONTROLEGASTOS_COOKIE_SECURE", "1")
    app = criar_app()

    assert (tmp_path / "fora" / "x.db").exists()
    assert app.state.config.cookie_secure is True
    assert app.state.config.chave_secreta == "k" * 40
