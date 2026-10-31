# Tecnologia

## Stack

- Python >= 3.14, gerenciado com [uv](https://docs.astral.sh/uv/)
- openpyxl para gerar o .xlsx (e os gráficos)
- pytest para testes e hypothesis para testes de propriedade
- ruff para lint
- Extra opcional `ui`: Streamlit, usado só pela interface web

## Comandos

```bash
uv sync                    # instala dependências (padrão + dev)
uv sync --extra ui         # inclui a interface web
uv run pytest              # testes
uv run ruff check .        # lint
uv run controlegastos gerar data/entradas/exemplo.json -o saida/planilha.xlsx
uv run controlegastos gerar data/entradas/exemplo.json -o saida/planilha.xlsx --formato ambos
uv run controlegastos ui   # interface web (requer o extra ui)
```

## Ambiente Windows

- `uv` e `git` foram instalados via winget. Em um terminal aberto antes da instalação, recarregue o PATH:
  `$env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User')`
- O shell padrão é PowerShell; prefira `;` a `&&` em comandos encadeados.

## CI

`.github/workflows/ci.yml` roda `uv sync`, `uv run ruff check .` e `uv run pytest` em Python 3.14. Um job não bloqueante confere se o extra `ui` instala.
