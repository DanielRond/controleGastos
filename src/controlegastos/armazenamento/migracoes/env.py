"""Ambiente do Alembic: usa a conexão entregue por `aplicar_migracoes` (sem alembic.ini)."""

from alembic import context

from controlegastos.armazenamento.modelos import Base

config = context.config
conexao = config.attributes.get("connection")

if conexao is None:  # pragma: no cover - o uso suportado é por aplicar_migracoes
    raise RuntimeError("Use controlegastos.armazenamento.aplicar_migracoes para migrar o banco.")

context.configure(connection=conexao, target_metadata=Base.metadata)
with context.begin_transaction():
    context.run_migrations()
