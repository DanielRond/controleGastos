"""Senhas (Argon2), cookie de sessão assinado e limite de tentativas de login (WEB-01 a WEB-03)."""

from __future__ import annotations

import time
from collections import defaultdict, deque
from collections.abc import Callable
from typing import Any

from itsdangerous import BadSignature, URLSafeTimedSerializer
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

SESSAO_SEGUNDOS = 7 * 24 * 3600
JANELA_SEGUNDOS = 15 * 60
MAX_FALHAS = 5

_hasher = PasswordHash((Argon2Hasher(),))
_HASH_FALSO = _hasher.hash("senha-que-nunca-sera-usada")  # gasta o mesmo tempo quando o usuário não existe


def gerar_hash(senha: str) -> str:
    return _hasher.hash(senha)


def verificar_hash(senha: str, hash_guardado: str) -> bool:
    try:
        return _hasher.verify(senha, hash_guardado)
    except Exception:  # noqa: BLE001 - hash inválido equivale a senha errada
        return False


def verificar_contra_falso(senha: str) -> None:
    """Equaliza o tempo de resposta entre usuário inexistente e senha errada."""
    verificar_hash(senha, _HASH_FALSO)


def _serializador(chave: str) -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(chave, salt="controlegastos-sessao")


def assinar_sessao(dados: dict[str, Any], chave: str) -> str:
    return _serializador(chave).dumps(dados)


def ler_sessao(token: str, chave: str, max_age: int = SESSAO_SEGUNDOS) -> dict[str, Any] | None:
    """Os dados da sessão, ou None se o cookie foi adulterado, é de outra chave ou expirou."""
    try:
        dados = _serializador(chave).loads(token, max_age=max_age)
    except BadSignature:  # inclui SignatureExpired
        return None
    return dados if isinstance(dados, dict) else None


class LimitadorDeLogin:
    """5 falhas em 15 minutos para a mesma chave (nome + IP) bloqueiam novas tentativas."""

    def __init__(self, relogio: Callable[[], float] = time.monotonic) -> None:
        self.relogio = relogio
        self._falhas: dict[tuple[str, str], deque[float]] = defaultdict(deque)

    def _recentes(self, chave: tuple[str, str]) -> deque[float]:
        falhas = self._falhas[chave]
        limite = self.relogio() - JANELA_SEGUNDOS
        while falhas and falhas[0] <= limite:
            falhas.popleft()
        return falhas

    def segundos_de_bloqueio(self, chave: tuple[str, str]) -> int:
        """0 se pode tentar; senão, quanto falta para a tentativa mais antiga sair da janela."""
        falhas = self._recentes(chave)
        if len(falhas) < MAX_FALHAS:
            return 0
        return max(1, int(falhas[0] + JANELA_SEGUNDOS - self.relogio()) + 1)

    def registrar_falha(self, chave: tuple[str, str]) -> None:
        self._recentes(chave).append(self.relogio())

    def registrar_sucesso(self, chave: tuple[str, str]) -> None:
        self._falhas.pop(chave, None)
