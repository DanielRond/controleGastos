"""Tabelas do banco (SQLAlchemy 2). O domínio (modelo.py) não conhece este módulo."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def agora() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class Usuario(Base):
    __tablename__ = "usuario"
    __table_args__ = (UniqueConstraint("nome", name="uq_usuario_nome"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(80))
    senha_hash: Mapped[str] = mapped_column(String(255))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)


class MesRegistro(Base):
    """Um mês de um usuário, com salário e meta opcionais (em centavos)."""

    __tablename__ = "mes"
    __table_args__ = (UniqueConstraint("usuario_id", "ano", "mes", name="uq_mes_usuario_ano_mes"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuario.id", ondelete="CASCADE"))
    ano: Mapped[int] = mapped_column(Integer)
    mes: Mapped[int] = mapped_column(Integer)
    salario_centavos: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    meta_investimento_centavos: Mapped[int | None] = mapped_column(BigInteger, nullable=True)


class LancamentoRegistro(Base):
    """Receita, despesa ou investimento. `apagado_em` preenchido = na lixeira (STO-12)."""

    __tablename__ = "lancamento"
    __table_args__ = (
        Index("ix_lancamento_usuario_apagado", "usuario_id", "apagado_em"),
        Index("ix_lancamento_mes_id", "mes_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuario.id", ondelete="CASCADE"))
    mes_id: Mapped[int] = mapped_column(ForeignKey("mes.id", ondelete="CASCADE"))
    tipo: Mapped[str] = mapped_column(String(20))
    descricao: Mapped[str] = mapped_column(String(255))
    valor_centavos: Mapped[int] = mapped_column(BigInteger)
    dia: Mapped[int] = mapped_column(Integer)
    categoria: Mapped[str] = mapped_column(String(80))
    tipo_investimento: Mapped[str | None] = mapped_column(String(20), nullable=True)
    ativo: Mapped[str | None] = mapped_column(String(80), nullable=True)
    origem: Mapped[str] = mapped_column(String(20))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)
    apagado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
