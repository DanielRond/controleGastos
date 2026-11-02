@AGENTS.md

## Claude Code

- O contexto do projeto está no `AGENTS.md` (importado acima); não duplique regras aqui.
- Subagentes em `.claude/agents/` são **gerados** a partir de `.kiro/agents/`: edite a fonte no Kiro e rode `uv run python scripts/sincronizar_agentes.py` (um teste falha se estiverem defasados).
- O hook de `.claude/settings.json` roda `scripts/checar.py` após editar arquivos; se falhar, corrija antes de seguir.
- `git commit` e `git push` pedem confirmação; commite só quando o usuário pedir ou autorizar.
