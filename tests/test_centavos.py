"""Conversão entre Decimal e centavos inteiros (armazenamento/centavos.py)."""

from decimal import Decimal

import pytest

pytest.importorskip("sqlalchemy")

from controlegastos.armazenamento.centavos import (
    de_centavos,
    para_centavos,
)


# Spec: STO-02
@pytest.mark.parametrize(
    ("valor", "centavos"),
    [("12.34", 1234), ("12.3", 1230), ("5", 500), ("0", 0), ("0.01", 1), ("-1.50", -150), ("1E+2", 10000), ("1.500", 150)],
)
def test_para_centavos_e_exato(valor: str, centavos: int) -> None:
    assert para_centavos(Decimal(valor)) == centavos


# Spec: STO-02
@pytest.mark.parametrize(("centavos", "texto"), [(1234, "12.34"), (100, "1.00"), (0, "0.00"), (-150, "-1.50"), (5, "0.05")])
def test_de_centavos_devolve_decimal_com_duas_casas(centavos: int, texto: str) -> None:
    valor = de_centavos(centavos)
    assert isinstance(valor, Decimal)
    assert str(valor) == texto


# Spec: STO-02
def test_float_nunca_e_aceito_como_dinheiro() -> None:
    with pytest.raises(TypeError, match="Decimal"):
        para_centavos(10.5)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="Decimal"):
        para_centavos(True)  # type: ignore[arg-type]


# Spec: STO-11
@pytest.mark.parametrize("valor", ["0.001", "10.123", "1.005", "99.999999"])
def test_mais_de_duas_casas_e_rejeitado_sem_arredondar(valor: str) -> None:
    with pytest.raises(ValueError, match="no máximo 2 casas decimais"):
        para_centavos(Decimal(valor))
