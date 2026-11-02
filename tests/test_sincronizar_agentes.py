"""Garante que os subagentes do Claude Code refletem os do Kiro."""

import importlib.util
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("sincronizar", RAIZ / "scripts" / "sincronizar_agentes.py")
sincronizar = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sincronizar)


def test_agentes_do_claude_estao_sincronizados_com_os_do_kiro() -> None:
    assert sincronizar.defasados() == [], "rode: uv run python scripts/sincronizar_agentes.py"


def test_conversao_mapeia_ferramentas_e_restricoes() -> None:
    kiro = (RAIZ / ".kiro" / "agents" / "qa.md").read_text(encoding="utf-8")
    claude = sincronizar.converter(kiro)
    assert "tools: Read, Grep, Glob, Write, Edit, Bash" in claude
    assert "Escreva somente em: `tests/**`." in claude
    assert "Nunca execute: `git push *`" in claude
    assert "git commit --no-verify *" in claude
    assert "`git commit *`" not in claude  # commits são permitidos
    assert "permissions:" not in claude
