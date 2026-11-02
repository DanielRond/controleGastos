---
inclusion: manual
---

# Revisar documentação

Acionado manualmente com `/revisar-documentacao` no chat.

Revise `README.md`, `AGENTS.md`, `CLAUDE.md`, `specs/README.md`, `specs/*/tasks.md` e os agentes em `.kiro/agents` contra o código atual:

1. Leia `src/controlegastos/*.py`, `pyproject.toml`, `scripts/`, `.github/workflows/ci.yml` e `specs/*/spec.md`.
2. Liste divergências: comandos, subcomandos, opções, módulos, dependências, esquema JSON, status dos specs, fases concluídas e roadmap.
3. Corrija apenas a documentação (não edite `spec.md`: proponha a mudança). O `AGENTS.md` é a fonte de verdade e deve continuar curto (~100 linhas).
4. Rode `uv run python scripts/sincronizar_agentes.py` se mexer em `.kiro/agents`.
5. Relate o que mudou e commite em branch `docs/`, conforme o `AGENTS.md`.
