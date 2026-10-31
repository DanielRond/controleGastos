"""Checagem rápida usada pelo hook de salvar: ruff em tudo e pytest só do módulo alterado.

Portável (Windows, Linux e macOS): não depende de sintaxe de shell.
O Kiro envia o contexto do evento em JSON na entrada padrão; se o arquivo
alterado não puder ser identificado, a suíte completa é executada.

Uso: uv run python scripts/checar.py
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PADRAO_PY = re.compile(r"[\w./\\:-]*\b(?:src|tests)[\\/][\w./\\-]*\.py")


def _arquivo_alterado() -> Path | None:
    """Extrai do JSON do evento o primeiro caminho .py em src/ ou tests/."""
    if sys.stdin is None or sys.stdin.isatty():
        return None
    bruto = sys.stdin.read()
    try:
        texto = json.dumps(json.loads(bruto)) if bruto.strip() else ""
    except ValueError:
        texto = bruto
    achado = PADRAO_PY.search(texto.replace("\\\\", "/").replace("\\", "/"))
    return Path(achado.group(0)) if achado else None


def _alvos_de_teste(arquivo: Path | None) -> list[str]:
    if arquivo is None:
        return []
    partes = arquivo.as_posix().split("/")
    if "tests" in partes:
        caminho = RAIZ / Path(*partes[partes.index("tests") :])
        return [str(caminho)] if caminho.is_file() else []
    modulo = arquivo.stem
    return sorted(str(p) for p in (RAIZ / "tests").glob(f"test_{modulo}*.py"))


def _rodar(comando: list[str]) -> int:
    print("$", " ".join(comando), flush=True)
    return subprocess.run(comando, cwd=RAIZ, check=False).returncode


def main() -> int:
    alvos = _alvos_de_teste(_arquivo_alterado())
    if _rodar(["uv", "run", "ruff", "check", "."]) != 0:
        return 1
    return 1 if _rodar(["uv", "run", "pytest", "-q", *alvos]) != 0 else 0


if __name__ == "__main__":
    sys.exit(main())
