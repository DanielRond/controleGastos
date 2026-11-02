"""Conexão e migrações do banco (STO-01, STO-07)."""

from __future__ import annotations

import os
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, create_engine, event
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

NOME_DO_ARQUIVO = "controlegastos.db"


def url_do_banco(url: str | None = None) -> str:
    """Argumento explícito, depois DATABASE_URL, depois um SQLite local em `dados/`."""
    if url:
        return url
    if os.environ.get("DATABASE_URL"):
        return os.environ["DATABASE_URL"]
    pasta = Path(os.environ.get("CONTROLEGASTOS_DADOS", "dados"))
    return f"sqlite:///{pasta / NOME_DO_ARQUIVO}"


def criar_engine(url: str | None = None) -> Engine:
    alvo = make_url(url_do_banco(url))
    opcoes: dict = {}
    if alvo.get_backend_name() == "sqlite":
        opcoes["connect_args"] = {"check_same_thread": False}
        if alvo.database in (None, "", ":memory:"):
            opcoes["poolclass"] = StaticPool  # a mesma conexão serve todos (banco só em memória)
        else:
            Path(alvo.database).parent.mkdir(parents=True, exist_ok=True)
    motor = create_engine(alvo, **opcoes)
    if alvo.get_backend_name() == "sqlite":

        @event.listens_for(motor, "connect")
        def _ativar_chaves_estrangeiras(conexao, _registro):
            cursor = conexao.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return motor


def criar_sessao(motor: Engine) -> Session:
    return Session(motor, expire_on_commit=False)


def _configuracao() -> Config:
    config = Config()
    config.set_main_option("script_location", str(Path(__file__).parent / "migracoes"))
    return config


def aplicar_migracoes(motor: Engine) -> None:
    """Leva o banco à versão mais nova do esquema; pode rodar quantas vezes quiser."""
    config = _configuracao()
    with motor.begin() as conexao:
        config.attributes["connection"] = conexao
        command.upgrade(config, "head")


def atualizar_banco(url: str | None = None) -> str:
    """Cria ou atualiza o esquema do banco indicado e devolve a URL (sem senha)."""
    motor = criar_engine(url)
    try:
        aplicar_migracoes(motor)
        return motor.url.render_as_string(hide_password=True)
    finally:
        motor.dispose()
