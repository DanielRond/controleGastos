"""Constrói a imagem Docker e confere o modo hospedado de verdade (WEB-15).

Sobe o contêiner com um volume novo e verifica: saúde, front servido, criação de conta por
`--senha-stdin`, login, gravação de um lançamento, execução sem root, app somente leitura e
persistência dos dados depois de reiniciar o contêiner. Limpa tudo no fim.

Só biblioteca padrão. Precisa de Docker.
Uso: python scripts/testar_imagem.py [--manter]
"""

from __future__ import annotations

import argparse
import http.cookiejar
import json
import secrets
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
IMAGEM = "controlegastos:teste"
SENHA = "senha-segura-123"


def docker(*args: str, entrada: str | None = None, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["docker", *args], input=entrada, text=True, capture_output=True, check=check, cwd=RAIZ)


def porta_livre() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class Cliente:
    """Cliente HTTP mínimo com cookies, para falar com o app como um navegador."""

    def __init__(self, base: str) -> None:
        self.base = base
        self.csrf = ""
        self.abridor = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))

    def chamar(self, metodo: str, caminho: str, corpo: object | None = None) -> tuple[int, bytes]:
        cabecalhos = {"Content-Type": "application/json"} if corpo is not None else {}
        if self.csrf and metodo != "GET":
            cabecalhos["X-CSRF-Token"] = self.csrf
        dados = json.dumps(corpo).encode() if corpo is not None else None
        requisicao = urllib.request.Request(self.base + caminho, data=dados, method=metodo, headers=cabecalhos)
        try:
            with self.abridor.open(requisicao, timeout=10) as resposta:
                return resposta.status, resposta.read()
        except urllib.error.HTTPError as erro:
            return erro.code, erro.read()


def esperar_saude(cliente: Cliente, segundos: int = 90) -> None:
    limite = time.time() + segundos
    while time.time() < limite:
        try:
            if cliente.chamar("GET", "/api/saude")[0] == 200:
                return
        except OSError:
            pass
        time.sleep(1)
    raise AssertionError("o contêiner não ficou saudável a tempo")


def conferir(condicao: bool, mensagem: str) -> None:
    if not condicao:
        raise AssertionError(mensagem)
    print(f"ok  {mensagem}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manter", action="store_true", help="não apaga contêiner e volume no fim")
    args = parser.parse_args()

    sufixo = secrets.token_hex(3)
    nome, volume, porta = f"cg-teste-{sufixo}", f"cg-dados-{sufixo}", porta_livre()
    try:
        print("construindo a imagem (pode demorar)...")
        docker("build", "-t", IMAGEM, ".")
        docker("volume", "create", volume)
        docker(
            "run", "-d", "--name", nome, "-p", f"127.0.0.1:{porta}:8000", "-v", f"{volume}:/data",
            "-e", f"CONTROLEGASTOS_CHAVE_SECRETA={secrets.token_urlsafe(48)}", "-e", "CONTROLEGASTOS_COOKIE_SECURE=0",
            IMAGEM,
        )
        cliente = Cliente(f"http://127.0.0.1:{porta}")
        esperar_saude(cliente)
        conferir(True, "responde em /api/saude")

        status, corpo = cliente.chamar("GET", "/")
        conferir(status == 200 and b'id="raiz"' in corpo, "serve o front compilado na raiz")
        conferir(cliente.chamar("GET", "/api/me")[0] == 401, "a API exige login")

        conferir(docker("exec", nome, "id", "-u").stdout.strip() != "0", "roda sem ser root")
        conferir(docker("exec", nome, "touch", "/app/x", check=False).returncode != 0, "o código do app é somente leitura")

        criar = docker("exec", "-i", nome, "controlegastos", "usuario", "criar", "ana", "--senha-stdin", entrada=SENHA + "\n")
        conferir("Usuário criado: ana" in criar.stdout, "cria a conta por --senha-stdin")

        status, corpo = cliente.chamar("POST", "/api/auth/login", {"nome": "ana", "senha": SENHA})
        conferir(status == 200, "faz login")
        cliente.csrf = json.loads(corpo)["csrf_token"]
        status, _ = cliente.chamar(
            "POST", "/api/lancamentos",
            {"ano": 2026, "mes": 11, "tipo": "despesa", "descricao": "Mercado", "valor": "100.50", "dia": 3},
        )
        conferir(status == 201, "grava um lançamento")

        docker("restart", nome)
        esperar_saude(cliente)
        novo = Cliente(f"http://127.0.0.1:{porta}")
        status, corpo = novo.chamar("POST", "/api/auth/login", {"nome": "ana", "senha": SENHA})
        conferir(status == 200, "a conta sobrevive ao reinício (dados no volume)")
        novo.csrf = json.loads(corpo)["csrf_token"]
        status, corpo = novo.chamar("GET", "/api/meses/2026/11")
        conferir(status == 200 and json.loads(corpo)["totais"]["despesas"] == "100.50", "o lançamento sobrevive ao reinício")

        saude = docker("inspect", "--format", "{{.State.Health.Status}}", nome).stdout.strip()
        deadline = time.time() + 60
        while saude != "healthy" and time.time() < deadline:
            time.sleep(2)
            saude = docker("inspect", "--format", "{{.State.Health.Status}}", nome).stdout.strip()
        conferir(saude == "healthy", "o HEALTHCHECK do Docker fica healthy")
        print("imagem ok")
        return 0
    except (AssertionError, subprocess.CalledProcessError) as erro:
        print(f"FALHOU: {erro}", file=sys.stderr)
        if isinstance(erro, subprocess.CalledProcessError):
            print((erro.stdout or "")[-2000:], (erro.stderr or "")[-3000:], file=sys.stderr)
        logs = docker("logs", nome, check=False)
        print("--- logs do contêiner ---\n" + (logs.stdout + logs.stderr)[-3000:], file=sys.stderr)
        return 1
    finally:
        if not args.manter:
            docker("rm", "-f", nome, check=False)
            docker("volume", "rm", "-f", volume, check=False)


if __name__ == "__main__":
    sys.exit(main())
