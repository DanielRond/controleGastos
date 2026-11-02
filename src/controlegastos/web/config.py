"""Configuração da aplicação web, lida de variáveis de ambiente (WEB-04, WEB-15)."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Configuracao:
    database_url: str | None = None  # None: DATABASE_URL ou o SQLite local (armazenamento.banco)
    chave_secreta: str | None = None  # assina o cookie de sessão
    cookie_secure: bool = False  # True quando servido por HTTPS (modo hospedado)

    @classmethod
    def do_ambiente(cls) -> Configuracao:
        return cls(
            database_url=os.environ.get("DATABASE_URL") or None,
            chave_secreta=os.environ.get("CONTROLEGASTOS_CHAVE_SECRETA") or None,
            cookie_secure=os.environ.get("CONTROLEGASTOS_COOKIE_SECURE", "") == "1",
        )
