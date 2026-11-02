---
inclusion: manual
---

# Revisar documentação

Acionado manualmente com `/revisar-documentacao` no chat.

Revise `README.md` e `AGENTS.md` contra o código atual:

1. Leia `src/controlegastos/*.py`, `pyproject.toml`, `scripts/` e `.github/workflows/ci.yml`.
2. Liste divergências: comandos, subcomandos, opções, módulos, dependências, esquema JSON e roadmap.
3. Corrija apenas a documentação. O `AGENTS.md` é a fonte de verdade e deve continuar curto (~100 linhas).
4. Relate o que mudou. Não crie commits.
