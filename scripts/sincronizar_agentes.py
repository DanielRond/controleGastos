"""Gera os subagentes do Claude Code (.claude/agents) a partir dos do Kiro (.kiro/agents).

A fonte é `.kiro/agents/*.md`. O Claude Code não tem restrição de caminho por
subagente, então as permissões do Kiro viram uma seção de instruções no texto.

Uso:
    uv run python scripts/sincronizar_agentes.py          # grava .claude/agents
    uv run python scripts/sincronizar_agentes.py --check  # falha se estiver defasado
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ORIGEM = RAIZ / ".kiro" / "agents"
DESTINO = RAIZ / ".claude" / "agents"

FERRAMENTAS = {"read": ["Read", "Grep", "Glob"], "write": ["Write", "Edit"], "shell": ["Bash"]}
CABECALHO = "<!-- Gerado por scripts/sincronizar_agentes.py a partir de .kiro/agents. Não edite aqui. -->"


def _dividir(texto: str) -> tuple[str, str]:
    achado = re.match(r"---\n(.*?)\n---\n(.*)", texto, re.DOTALL)
    if not achado:
        raise ValueError("agente sem front matter")
    return achado.group(1), achado.group(2).lstrip("\n")


def _campo(frente: str, nome: str) -> str:
    achado = re.search(rf"^\s*{nome}:\s*(.+)$", frente, re.MULTILINE)
    if not achado:
        raise ValueError(f"campo '{nome}' ausente")
    return achado.group(1).strip()


def _regras(frente: str) -> list[dict]:
    """Lê `permissions.rules` (formato fixo: capability, match, exclude, effect)."""
    regras: list[dict] = []
    for bloco in re.split(r"^\s+- capability:", frente, flags=re.MULTILINE)[1:]:
        regra: dict = {"capability": bloco.splitlines()[0].strip()}
        for chave in ("match", "exclude"):
            achado = re.search(rf"^\s+{chave}:\s*(\[.*\])\s*$", bloco, re.MULTILINE)
            regra[chave] = json.loads(achado.group(1)) if achado else []
        regra["effect"] = _campo(bloco, "effect") if re.search(r"^\s*effect:", bloco, re.MULTILINE) else ""
        regras.append(regra)
    return regras


def _restricoes(regras: list[dict]) -> str:
    linhas: list[str] = []
    for r in regras:
        itens = ", ".join(f"`{m}`" for m in r["match"])
        if r["capability"] == "fs_write" and r["effect"] == "allow":
            linhas.append(f"- Escreva somente em: {itens}.")
        elif r["capability"] == "fs_write" and r["effect"] == "deny" and not r["exclude"]:
            linhas.append(f"- Nunca escreva em: {itens}.")
        elif r["capability"] == "shell" and r["effect"] == "deny":
            linhas.append(f"- Nunca execute: {itens}.")
        elif r["effect"] == "deny" and not (r["capability"] == "fs_write" and r["exclude"]):
            # deny de escrita "tudo, exceto X" já está coberto pelo allow de X
            linhas.append(f"- Proibido em {r['capability']}: {itens}.")
    if not linhas:
        return ""
    return "\n\n## Restrições (instrução; o Claude Code não as impõe sozinho)\n\n" + "\n".join(linhas) + "\n"


def converter(texto: str) -> str:
    frente, corpo = _dividir(texto)
    tools = re.findall(r'"(\w+)"', _campo(frente, "tools"))
    ferramentas = ", ".join(f for t in tools for f in FERRAMENTAS[t])
    descricao = _campo(frente, "description")
    saida = (
        f"---\nname: {_campo(frente, 'name')}\ndescription: {descricao}\ntools: {ferramentas}\n---\n"
        f"{CABECALHO}\n\n{corpo.rstrip()}{_restricoes(_regras(frente))}"
    )
    return saida if saida.endswith("\n") else saida + "\n"


def esperado() -> dict[str, str]:
    return {p.name: converter(p.read_text(encoding="utf-8")) for p in sorted(ORIGEM.glob("*.md"))}


def defasados() -> list[str]:
    alvo = esperado()
    ruins = [n for n, t in alvo.items() if not (DESTINO / n).is_file() or (DESTINO / n).read_text(encoding="utf-8") != t]
    ruins += [p.name for p in DESTINO.glob("*.md") if p.name not in alvo] if DESTINO.is_dir() else []
    return ruins


def main(argv: list[str]) -> int:
    if "--check" in argv:
        ruins = defasados()
        if ruins:
            print("Agentes do Claude Code defasados: " + ", ".join(ruins), file=sys.stderr)
            print("Rode: uv run python scripts/sincronizar_agentes.py", file=sys.stderr)
            return 1
        return 0
    DESTINO.mkdir(parents=True, exist_ok=True)
    alvo = esperado()
    for nome, texto in alvo.items():
        (DESTINO / nome).write_text(texto, encoding="utf-8", newline="\n")
    for velho in DESTINO.glob("*.md"):
        if velho.name not in alvo:
            velho.unlink()
    print(f"{len(alvo)} agentes gerados em {DESTINO.relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
