"""Testes da interface de linha de comando (cli.py)."""

import sys
from pathlib import Path

from controlegastos.cli import main

RAIZ = Path(__file__).resolve().parent.parent
EXEMPLO = RAIZ / "data" / "entradas" / "exemplo.json"


def test_main_entrada_valida(tmp_path: Path, monkeypatch) -> None:
    destino = tmp_path / "planilha-test.xlsx"
    monkeypatch.setattr(
        sys,
        "argv",
        ["controlegastos", "gerar", str(EXEMPLO), "-o", str(destino)],
    )

    assert main() == 0
    assert destino.exists()


def test_main_entrada_inexistente(tmp_path: Path, monkeypatch) -> None:
    destino = tmp_path / "planilha-test.xlsx"
    monkeypatch.setattr(
        sys,
        "argv",
        ["controlegastos", "gerar", str(tmp_path / "nao-existe.json"), "-o", str(destino)],
    )

    assert main() == 1
    assert not destino.exists()