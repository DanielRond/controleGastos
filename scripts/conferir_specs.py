"""Confere a rastreabilidade entre specs vigentes e testes.

Regras:
- todo ID definido (`**XXX-NN**`) em `specs/*/spec.md` com `status: vigente`
  deve ser citado em algum teste (`# Spec: XXX-NN` em `tests/`);
- todo ID citado em um teste deve existir em algum spec;
- IDs não se repetem dentro dos specs.

Uso: uv run python scripts/conferir_specs.py   (sai com 1 se houver problemas)
"""

from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ID = r"[A-Z]{3}-\d{2}"
DEFINICAO = re.compile(rf"\*\*({ID})\*\*")
CITACAO = re.compile(r"^\s*#\s*Spec:\s*(.+)$", re.MULTILINE)


def ids_definidos() -> tuple[set[str], Counter]:
    """IDs dos specs vigentes e a contagem de definições de todos os specs."""
    vigentes: set[str] = set()
    contagem: Counter = Counter()
    for arquivo in sorted((RAIZ / "specs").glob("*/spec.md")):
        texto = arquivo.read_text(encoding="utf-8")
        ids = DEFINICAO.findall(texto)
        contagem.update(ids)
        if re.search(r"^status:\s*vigente\b", texto, re.MULTILINE):
            vigentes.update(ids)
    return vigentes, contagem


def ids_citados() -> set[str]:
    citados: set[str] = set()
    for arquivo in sorted((RAIZ / "tests").glob("test_*.py")):
        for linha in CITACAO.findall(arquivo.read_text(encoding="utf-8")):
            citados.update(re.findall(ID, linha))
    return citados


def problemas() -> list[str]:
    vigentes, contagem = ids_definidos()
    citados = ids_citados()
    erros = [f"{i}: definido {n} vezes nos specs" for i, n in sorted(contagem.items()) if n > 1]
    erros += [f"{i}: requisito vigente sem teste (cite com '# Spec: {i}')" for i in sorted(vigentes - citados)]
    erros += [f"{i}: citado em teste, mas não existe em nenhum spec" for i in sorted(citados - set(contagem))]
    return erros


def main() -> int:
    erros = problemas()
    for erro in erros:
        print(erro, file=sys.stderr)
    if not erros:
        vigentes, _ = ids_definidos()
        print(f"specs ok: {len(vigentes)} requisitos vigentes, todos com teste")
    return 1 if erros else 0


if __name__ == "__main__":
    sys.exit(main())
