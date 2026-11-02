# syntax=docker/dockerfile:1

# ---- Estágio 1: compila o front-end (Node) ------------------------------------------------
FROM node:24-slim AS front
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
# o Vite grava a saída em ../src/controlegastos/web/static
RUN npm run build

# ---- Estágio 2: app Python 3.14 ------------------------------------------------------------
FROM python:3.14-slim AS app
RUN pip install --no-cache-dir "uv>=0.12.5,<0.13"
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never PYTHONUNBUFFERED=1
WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
COPY src ./src
COPY --from=front /app/src/controlegastos/web/static ./src/controlegastos/web/static
RUN uv sync --frozen --no-dev --no-editable --extra web

ENV PATH="/app/.venv/bin:$PATH" \
    CONTROLEGASTOS_DADOS=/data

# Sem root: o app só escreve em /data (banco SQLite)
RUN useradd --system --uid 10001 --no-create-home app && mkdir /data && chown app /data
USER app
VOLUME ["/data"]
EXPOSE 8000

# Configuração só por variáveis de ambiente (DATABASE_URL, CONTROLEGASTOS_CHAVE_SECRETA, CONTROLEGASTOS_COOKIE_SECURE)
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/saude', timeout=3)"]

CMD ["controlegastos", "web", "--host", "0.0.0.0", "--porta", "8000"]
