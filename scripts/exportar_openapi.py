"""Gera o instantâneo do contrato da API em specs/api/openapi.json (WEB-16).

O teste `test_openapi_...` falha se o arquivo estiver defasado; rode este script para atualizá-lo.
O cliente TypeScript do front-end é gerado a partir dele.

Uso: uv run python scripts/exportar_openapi.py
"""

from __future__ import annotations

import json
from pathlib import Path

from controlegastos.web import Configuracao, criar_app

DESTINO = Path(__file__).resolve().parent.parent / "specs" / "api" / "openapi.json"


def main() -> int:
    app = criar_app(Configuracao(database_url="sqlite://", chave_secreta="exportar-openapi"))
    DESTINO.write_text(json.dumps(app.openapi(), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"OpenAPI gravado em {DESTINO}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
