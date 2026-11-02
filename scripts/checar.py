"""Checagem rápida pós-edição, compartilhada pelo Kiro e pelo Claude Code.

Os dois enviam o contexto do evento em JSON na entrada padrão; o caminho do
arquivo editado é procurado em qualquer valor de texto do JSON (os nomes dos
campos variam entre ferramentas). Regras:

- `.py` em `src/` ou `tests/`: ruff em tudo e pytest só do módulo alterado;
- `data/entradas/exemplo*.json`: ruff e suíte completa (o esquema pode ter mudado);
- `.ts`/`.tsx` em `frontend/src` ou `frontend/e2e`: lint, tipos e testes relacionados (precisa de Node 24+
  no PATH; sem `npm`, avisa e não bloqueia);
- qualquer outro arquivo, ou entrada ilegível: não faz nada (saída 0).

Sucesso: uma linha na saída padrão. Falha: saída dos comandos em stderr e
código 2, que é o que o Claude Code e o Kiro devolvem ao agente.
Portável (Windows, Linux e macOS): sem sintaxe de shell.

Uso: uv run python scripts/checar.py
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PADRAO_PY = re.compile(r"(?:^|/)((?:src|tests)/[\w./-]*\.py)$")
PADRAO_EXEMPLO = re.compile(r"(?:^|/)data/entradas/exemplo[\w-]*\.json$")
PADRAO_TS = re.compile(r"(?:^|/)(frontend/(?:src|e2e)/[\w./-]*\.tsx?)$")


def _textos(valor: object) -> Iterator[str]:
    """Todos os textos de um JSON, em profundidade."""
    if isinstance(valor, str):
        yield valor
    elif isinstance(valor, dict):
        for item in valor.values():
            yield from _textos(item)
    elif isinstance(valor, list):
        for item in valor:
            yield from _textos(item)


def classificar(evento: object) -> tuple[str, str | None]:
    """Devolve ('py'|'ts', caminho_relativo), ('esquema', None) ou ('ignorar', None)."""
    for texto in _textos(evento):
        normal = texto.replace("\\", "/")
        achado = PADRAO_PY.search(normal)
        if achado:
            return "py", achado.group(1)
        if PADRAO_EXEMPLO.search(normal):
            return "esquema", None
        achado_ts = PADRAO_TS.search(normal)
        if achado_ts and "node_modules" not in normal and not normal.endswith(".d.ts"):
            return "ts", achado_ts.group(1)
    return "ignorar", None


def alvos_de_teste(caminho: str) -> list[str]:
    """Arquivos de teste que cobrem o arquivo alterado."""
    arquivo = RAIZ / caminho
    if caminho.startswith("tests/"):
        return [str(arquivo)] if arquivo.is_file() else []
    return sorted(str(p) for p in (RAIZ / "tests").glob(f"test_{arquivo.stem}*.py"))


def comandos_do_frontend(caminho: str) -> list[tuple[list[str], Path]]:
    """Lint, tipos e testes relacionados ao arquivo, todos rodando dentro de `frontend/`."""
    pasta = RAIZ / "frontend"
    relativo = caminho.removeprefix("frontend/")
    return [
        (["npm", "run", "lint"], pasta),
        (["npm", "run", "typecheck"], pasta),
        (["npx", "vitest", "related", "--run", relativo], pasta),
    ]


def _ler_evento() -> object:
    if sys.stdin is None or sys.stdin.isatty():
        return None
    bruto = sys.stdin.read()
    try:
        return json.loads(bruto) if bruto.strip() else None
    except ValueError:
        return None


def _rodar(comando: list[str], cwd: Path = RAIZ) -> tuple[int, str]:
    resultado = subprocess.run(
        comando, cwd=cwd, check=False, capture_output=True, text=True, encoding="utf-8"
    )
    return resultado.returncode, f"$ {' '.join(comando)}\n{resultado.stdout}{resultado.stderr}"


def _executar(comandos: list[tuple[list[str], Path]]) -> int:
    for argv, cwd in comandos:
        codigo, saida = _rodar(argv, cwd)
        if codigo != 0:
            print(saida, file=sys.stderr)
            return 2
    return 0


def main() -> int:
    tipo, caminho = classificar(_ler_evento())
    if tipo == "ignorar":
        return 0
    if tipo == "ts":
        if shutil.which("npm") is None:
            print("checar: npm não encontrado; instale o Node 24+ para checar o front-end (arquivo não verificado)", file=sys.stderr)
            return 0
        if _executar(comandos_do_frontend(caminho)) != 0:
            return 2
        print("checar: lint, tipos e testes do front-end ok")
        return 0
    alvos = alvos_de_teste(caminho) if caminho else []
    python = [
        (["uv", "run", "ruff", "check", "--no-cache", "."], RAIZ),
        (["uv", "run", "pytest", "-q", *alvos], RAIZ),
    ]
    if _executar(python) != 0:
        return 2
    print("checar: ruff e pytest ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
