"""Usuários. O hash da senha é gerado pela camada de autenticação (Fase 3), não aqui."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from .modelos import Usuario


def criar_usuario(sessao: Session, nome: str, senha_hash: str) -> int:
    """Cria o usuário e devolve o id; o nome é único."""
    nome = nome.strip()
    if not nome:
        raise ValueError("o nome do usuário não pode ficar vazio")
    if sessao.scalar(select(Usuario.id).where(Usuario.nome == nome)) is not None:
        raise ValueError(f"o usuário '{nome}' já existe")
    usuario = Usuario(nome=nome, senha_hash=senha_hash)
    sessao.add(usuario)
    sessao.commit()
    return usuario.id
