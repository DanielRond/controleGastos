"""Esquema inicial: usuário, mês e lançamento.

Revision ID: 0001
Revises:
"""

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "usuario",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nome", sa.String(80), nullable=False),
        sa.Column("senha_hash", sa.String(255), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("nome", name="uq_usuario_nome"),
    )
    op.create_table(
        "mes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("usuario.id", ondelete="CASCADE"), nullable=False),
        sa.Column("ano", sa.Integer(), nullable=False),
        sa.Column("mes", sa.Integer(), nullable=False),
        sa.Column("salario_centavos", sa.BigInteger(), nullable=True),
        sa.Column("meta_investimento_centavos", sa.BigInteger(), nullable=True),
        sa.UniqueConstraint("usuario_id", "ano", "mes", name="uq_mes_usuario_ano_mes"),
    )
    op.create_table(
        "lancamento",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("usuario.id", ondelete="CASCADE"), nullable=False),
        sa.Column("mes_id", sa.Integer(), sa.ForeignKey("mes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tipo", sa.String(20), nullable=False),
        sa.Column("descricao", sa.String(255), nullable=False),
        sa.Column("valor_centavos", sa.BigInteger(), nullable=False),
        sa.Column("dia", sa.Integer(), nullable=False),
        sa.Column("categoria", sa.String(80), nullable=False),
        sa.Column("tipo_investimento", sa.String(20), nullable=True),
        sa.Column("ativo", sa.String(80), nullable=True),
        sa.Column("origem", sa.String(20), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("apagado_em", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_lancamento_usuario_apagado", "lancamento", ["usuario_id", "apagado_em"])
    op.create_index("ix_lancamento_mes_id", "lancamento", ["mes_id"])


def downgrade() -> None:
    op.drop_index("ix_lancamento_mes_id", table_name="lancamento")
    op.drop_index("ix_lancamento_usuario_apagado", table_name="lancamento")
    op.drop_table("lancamento")
    op.drop_table("mes")
    op.drop_table("usuario")
