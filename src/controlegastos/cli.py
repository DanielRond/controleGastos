"""Interface de linha de comando do controle de gastos.

Uso:
    uv run controlegastos gerar data/entradas/exemplo.json -o saida/planilha.xlsx
    uv run controlegastos gerar data/entradas/exemplo.json -o saida/planilha.xlsx --formato ambos
    uv run controlegastos banco atualizar   # requer o extra web
    uv run controlegastos usuario criar NOME # requer o extra web
    uv run controlegastos web                # interface web em http://127.0.0.1:8000 (extra web)
"""

from __future__ import annotations

import argparse
import getpass
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

    usuario = subparsers.add_parser("usuario", help="Contas de acesso à interface web (requer o extra 'web').")
    acoes_usuario = usuario.add_subparsers(dest="acao", required=True, parser_class=_Parser)
    criar = acoes_usuario.add_parser("criar", help="Cria uma conta (a senha é pedida sem eco).")
    criar.add_argument("nome", help="Nome de usuário (único).")
    criar.add_argument("--senha-stdin", action="store_true", help="Lê a senha da entrada padrão (scripts e contêineres).")

    web = subparsers.add_parser("web", help="Sobe a interface web (API e telas) neste computador (requer o extra 'web').")
    web.add_argument("--host", default="127.0.0.1", help="Endereço de escuta (padrão: 127.0.0.1, só esta máquina).")
    web.add_argument("--porta", type=int, default=8000, help="Porta (padrão: 8000).")
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


def _executar_usuario(args: argparse.Namespace) -> int:
    logging.getLogger("alembic").setLevel(logging.WARNING)
    try:
        from .armazenamento import (
            aplicar_migracoes,
            criar_engine,
            criar_sessao,
            criar_usuario,
        )
        from .web.seguranca import gerar_hash
    except ImportError:
        logger.error("Os comandos de usuário exigem o extra web. Instale com: uv sync --extra web")
        return 1

    if args.senha_stdin:
        senha = sys.stdin.readline().rstrip("\r\n")
    else:
        senha = getpass.getpass("Senha: ")
        confirmacao = getpass.getpass("Repita a senha: ")
        if senha != confirmacao:
            logger.error("As senhas não conferem.")
            return 1
    if len(senha) < 8:
        logger.error("A senha deve ter ao menos 8 caracteres.")
        return 1

    motor = criar_engine()
    try:
        aplicar_migracoes(motor)
        with criar_sessao(motor) as sessao:
            criar_usuario(sessao, args.nome, gerar_hash(senha))
    except ValueError as erro:
        logger.error("%s", erro)
        return 1
    finally:
        motor.dispose()
    print(f"Usuário criado: {args.nome.strip()}")
    return 0


def _executar_web(args: argparse.Namespace) -> int:
    logging.getLogger("alembic").setLevel(logging.WARNING)
    try:
        import uvicorn

        from .web import Configuracao, criar_app
        from .web import app as modulo_app
    except ImportError:
        logger.error("A interface web exige o extra web. Instale com: uv sync --extra web")
        return 1

    config = Configuracao.do_ambiente()
    if args.host not in ("127.0.0.1", "localhost", "::1") and not config.cookie_secure:
        logger.warning(
            "Escutando em %s sem HTTPS configurado: defina CONTROLEGASTOS_COOKIE_SECURE=1 e "
            "CONTROLEGASTOS_CHAVE_SECRETA e coloque um proxy HTTPS na frente (veja docs/hospedagem.md).",
            args.host,
        )
    if not (modulo_app.PASTA_DO_FRONT / "index.html").is_file():
        logger.warning("Front-end não compilado: só a API será servida. Compile com: cd frontend && npm ci && npm run build")
    try:
        app = criar_app(config)
    except RuntimeError as erro:
        logger.error("%s", erro)
        return 1
    print(f"Interface disponível em http://{args.host}:{args.porta}")
    uvicorn.run(app, host=args.host, port=args.porta, log_level="info")
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
    if args.comando == "usuario":
        return _executar_usuario(args)
    if args.comando == "web":
        return _executar_web(args)
    return _executar_gerar(args)


if __name__ == "__main__":
    sys.exit(main())
