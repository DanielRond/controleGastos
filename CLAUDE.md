@AGENTS.md

## Claude Code

- O contexto do projeto está no `AGENTS.md` (importado acima); não duplique regras aqui.
- Subagentes em `.claude/agents/` são **gerados** a partir de `.kiro/agents/`: edite a fonte no Kiro e rode `uv run python scripts/sincronizar_agentes.py` (um teste falha se estiverem defasados).
- O hook de `.claude/settings.json` roda `scripts/checar.py` após editar arquivos; se falhar, corrija antes de seguir. O lembrete de esquema do Kiro não existe aqui: siga a regra 4 do `AGENTS.md`.
- Commits seguem a regra 2 do `AGENTS.md` (autônomos, em branch, nunca na `main`). `git push --force`, `git reset --hard` e `git clean` pedem confirmação.
