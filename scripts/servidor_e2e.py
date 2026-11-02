"""Sobe o app de verdade (API + front compilado) para os testes de ponta a ponta do Playwright.

Usa um SQLite temporário e cria a conta `ana` / `senha-segura-123`. O front precisa estar compilado
(`cd frontend && npm run build`). Não use fora dos testes: a senha é conhecida.

Uso: uv run python scripts/servidor_e2e.py [--porta 8765]
"""

from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

import uvicorn

from controlegastos.armazenamento import criar_sessao, criar_usuario
from controlegastos.web import Configuracao, criar_app
from controlegastos.web.seguranca import gerar_hash


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--porta", type=int, default=8765)
    args = parser.parse_args()

    pasta = Path(tempfile.mkdtemp(prefix="controlegastos-e2e-"))
    app = criar_app(Configuracao(database_url=f"sqlite:///{pasta / 'e2e.db'}", chave_secreta="e2e-" * 12))
    with criar_sessao(app.state.motor) as sessao:
        criar_usuario(sessao, "ana", gerar_hash("senha-segura-123"))
    uvicorn.run(app, host="127.0.0.1", port=args.porta, log_level="warning")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
