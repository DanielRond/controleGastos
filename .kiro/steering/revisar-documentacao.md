---
inclusion: manual
---

# Revisar documentação

Acionado manualmente com `/revisar-documentacao` no chat.

Revise `README.md`, `AGENTS.md` e `.kiro/steering/*.md` contra o código atual:

1. Leia `src/controlegastos/*.py`, `pyproject.toml` e `.github/workflows/ci.yml`.
2. Liste divergências: comandos, subcomandos, opções, módulos, dependências, esquema JSON e roadmap.
3. Corrija apenas a documentação. O `AGENTS.md` é a fonte de verdade para o steering.
4. Relate o que mudou. Não crie commits.
