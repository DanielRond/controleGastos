"""Interface de linha de comando do controle de gastos.

Uso:
    uv run controlegastos gerar data/entradas/exemplo.json -o saida/planilha.xlsx
    uv run controlegastos gerar data/entradas/exemplo.json -o saida/planilha.xlsx --formato ambos
    uv run controlegastos banco atualizar   # requer o extra web
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from . import servico
from .servico import FORMATOS, ErroDeValidacaoJSON

logger = logging.getLogger(__name__)


class _Parser(argparse.ArgumentParser):
    """ArgumentParser com mensagem em português para valores inválidos de --formato."""

    def error(self, message: str) -> None:  # type: ignore[override]
        if "--formato" in message:
            message = f"Valor inválido para --formato. Use: {', '.join(FORMATOS)}."
        super().error(message)


def _montar_parser() -> argparse.ArgumentParser:
    parser = _Parser(
        prog="controlegastos",
        description="Gera planilhas de controle de gastos a partir de arquivos JSON.",
    )
    subparsers = parser.add_subparsers(dest="comando", required=True, parser_class=_Parser)

    gerar = subparsers.add_parser("gerar", help="Gera a planilha a partir de um arquivo JSON.")
    gerar.add_argument("entrada", type=Path, help="Caminho do JSON com os lançamentos.")
    gerar.add_argument("-o", "--saida", type=Path, default=Path("saida/planilha.xlsx"))
    gerar.add_argument(
        "--formato",
        choices=FORMATOS,
        default="xlsx",
        help="Formato de saída: xlsx (padrão), csv ou ambos.",
    )
    gerar.add_argument("-v", "--verbose", action="store_true", help="Habilita log detalhado.")


    banco = subparsers.add_parser("banco", help="Comandos do banco de dados (requer o extra 'web').")
    acoes = banco.add_subparsers(dest="acao", required=True, parser_class=_Parser)
    acoes.add_parser("atualizar", help="Cria ou atualiza o esquema do banco (migrações).")
    return parser


def _executar_gerar(args: argparse.Namespace) -> int:
    try:
        livros = servico.carregar_arquivo(args.entrada)
    except ErroDeValidacaoJSON as erro:
        logger.error("O arquivo de entrada tem %d erro(s):", len(erro.erros))
        for item in erro.erros:
            logger.error("  - %s", item)
        return 1
    except (FileNotFoundError, KeyError, ValueError, TypeError) as erro:
        logger.error("Falha ao processar os dados: %s", erro)
        return 1

    try:
        gerados = servico.gerar_arquivos(livros, args.saida, args.formato)
    except OSError as erro:
        logger.error("Falha ao gravar os arquivos: %s", erro)
        return 1

    rotulo = "Planilha disponível em" if args.formato == "xlsx" else "Arquivo disponível em"
    for caminho in gerados:
        print(f"{rotulo}: {caminho}")
    return 0


def _executar_banco(args: argparse.Namespace) -> int:
    logging.getLogger("alembic").setLevel(logging.WARNING)  # sem o ruído interno das migrações
    try:
        from .armazenamento import atualizar_banco
    except ImportError:
        logger.error("Os comandos de banco exigem o extra web. Instale com: uv sync --extra web")
        return 1
    try:
        destino = atualizar_banco()
    except Exception as erro:  # noqa: BLE001 - qualquer falha de conexão/migração vira mensagem
        logger.error("Falha ao atualizar o banco: %s", erro)
        return 1
    print(f"Banco atualizado: {destino}")
    return 0


def main() -> int:
    parser = _montar_parser()
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if getattr(args, "verbose", False) else logging.INFO,
        format="%(levelname)s %(message)s",
    )

    if args.comando == "banco":
        return _executar_banco(args)
    return _executar_gerar(args)


if __name__ == "__main__":
    sys.exit(main())
