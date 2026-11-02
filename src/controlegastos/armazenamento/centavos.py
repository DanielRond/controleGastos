"""Conversão entre Decimal e centavos inteiros (STO-02, STO-11).

Dinheiro é guardado como inteiro em centavos e nunca passa por float.
"""

from __future__ import annotations

from decimal import Decimal

from ..validador import casas_decimais


def para_centavos(valor: Decimal) -> int:
    """Converte um Decimal com no máximo 2 casas em centavos; nunca arredonda em silêncio."""
    if isinstance(valor, bool) or not isinstance(valor, Decimal):
        raise TypeError("dinheiro deve ser Decimal, nunca float ou outro tipo")
    if not valor.is_finite():
        raise ValueError("valor deve ser finito")
    if casas_decimais(valor) > 2:
        raise ValueError("valor deve ter no máximo 2 casas decimais")
    return int(valor.scaleb(2))


def de_centavos(centavos: int) -> Decimal:
    """Centavos inteiros em Decimal com duas casas (1234 -> Decimal('12.34'))."""
    return Decimal(centavos).scaleb(-2)
