"""Interface de linha de comando do controle de gastos.

Uso:
    uv run controlegastos gerar data/entradas/exemplo.json -o saida/planilha.xlsx
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from .generator import gerar_planilha
from .loader import carregar_json

logger = logging.getLogger(__name__)


def _montar_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="controlegastos",
        description="Gera planilhas de controle de gastos a partir de arquivos JSON.",
    )
    subparsers = parser.add_subparsers(dest="comando", required=True)

    gerar = subparsers.add_parser("gerar", help="Gera a planilha a partir de um arquivo JSON.")
    gerar.add_argument("entrada", type=Path, help="Caminho do JSON com os lançamentos.")
    gerar.add_argument("-o", "--saida", type=Path, default=Path("saida/planilha.xlsx"))
    gerar.add_argument("-v", "--verbose", action="store_true", help="Habilita log detalhado.")
    return parser


def main() -> int:
    parser = _montar_parser()
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if getattr(args, "verbose", False) else logging.INFO,
        format="%(levelname)s %(message)s",
    )

    try:
        livros = carregar_json(args.entrada)
        destino = gerar_planilha(livros, args.saida)
    except (FileNotFoundError, KeyError, ValueError, TypeError) as erro:
        logger.error("Falha ao processar os dados: %s", erro)
        return 1

    print(f"Planilha disponível em: {destino}")
    return 0


if __name__ == "__main__":
    sys.exit(main())