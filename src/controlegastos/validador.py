"""Validação do esquema do JSON de entrada.

Usa apenas a biblioteca padrão e não importa outros módulos do pacote.
Dinheiro no JSON tem no máximo duas casas decimais (VAL-13).
"""

import calendar
import math
from dataclasses import dataclass
from decimal import Decimal

TIPOS_DE_INVESTIMENTO_CONHECIDOS: frozenset[str] = frozenset({"renda_fixa", "fii", "cripto"})

_RAIZ = "(raiz)"


@dataclass(frozen=True, slots=True)
class ErroDeValidacao:
    """Um erro de validação, com o caminho do campo e a mensagem em português."""

    caminho: str
    mensagem: str

    def __str__(self) -> str:
        return f"{self.caminho}: {self.mensagem}"


def _inteiro(valor: object) -> bool:
    return isinstance(valor, int) and not isinstance(valor, bool)


def _numero_finito(valor: object) -> bool:
    return (
        isinstance(valor, (int, float))
        and not isinstance(valor, bool)
        and math.isfinite(valor)
    )


def _junta(base: str, campo: str) -> str:
    return f"{base}.{campo}" if base else campo


def casas_decimais(valor: float | Decimal) -> int:
    """Quantidade de casas decimais significativas (sem contar zeros à direita): 1.500 -> 1."""
    _, digitos, expoente = Decimal(str(valor)).as_tuple()
    if not isinstance(expoente, int) or expoente >= 0:
        return 0
    zeros = 0
    for digito in reversed(digitos):
        if digito != 0 or zeros >= -expoente:
            break
        zeros += 1
    return -expoente - zeros


def _validar_numero(obj: dict, campo: str, base: str, erros: list[ErroDeValidacao]) -> None:
    if campo not in obj:
        return
    if not _numero_finito(obj[campo]):
        erros.append(
            ErroDeValidacao(
                _junta(base, campo), f"{campo} deve ser numérico finito (não booleano)"
            )
        )
    elif casas_decimais(obj[campo]) > 2:
        erros.append(
            ErroDeValidacao(_junta(base, campo), f"{campo} deve ter no máximo 2 casas decimais")
        )


def _validar_texto_opcional(
    obj: dict, campo: str, base: str, erros: list[ErroDeValidacao]
) -> None:
    if campo in obj and not isinstance(obj[campo], str):
        erros.append(ErroDeValidacao(_junta(base, campo), f"{campo} deve ser texto"))


def _validar_lancamento(
    item: object,
    caminho: str,
    investimento: bool,
    ano: int | None,
    mes: int | None,
    erros: list[ErroDeValidacao],
) -> None:
    if not isinstance(item, dict):
        erros.append(ErroDeValidacao(caminho, "lançamento deve ser um objeto"))
        return

    obrigatorios = ["tipo"] if investimento else []
    obrigatorios += ["descricao", "valor", "dia"]
    for campo in obrigatorios:
        if campo not in item:
            erros.append(
                ErroDeValidacao(_junta(caminho, campo), f"campo obrigatório '{campo}' ausente")
            )

    if investimento and "tipo" in item:
        tipo = item["tipo"]
        if not isinstance(tipo, str) or tipo not in TIPOS_DE_INVESTIMENTO_CONHECIDOS:
            conhecidos = ", ".join(sorted(TIPOS_DE_INVESTIMENTO_CONHECIDOS))
            erros.append(
                ErroDeValidacao(
                    _junta(caminho, "tipo"),
                    f"tipo de investimento desconhecido; use um de: {conhecidos}",
                )
            )

    if "descricao" in item and not isinstance(item["descricao"], str):
        erros.append(ErroDeValidacao(_junta(caminho, "descricao"), "descricao deve ser texto"))

    _validar_numero(item, "valor", caminho, erros)

    if "dia" in item:
        dia = item["dia"]
        if not _inteiro(dia):
            erros.append(ErroDeValidacao(_junta(caminho, "dia"), "dia deve ser um inteiro"))
        elif ano is not None and mes is not None:
            ultimo = calendar.monthrange(ano, mes)[1]
            if not 1 <= dia <= ultimo:
                erros.append(
                    ErroDeValidacao(
                        _junta(caminho, "dia"),
                        f"dia {dia} é inválido para {mes:02d}/{ano} (esperado entre 1 e {ultimo})",
                    )
                )

    _validar_texto_opcional(item, "categoria", caminho, erros)
    if investimento:
        _validar_texto_opcional(item, "ativo", caminho, erros)


def _validar_mes(
    mes_obj: object, caminho: str, ano: int | None, erros: list[ErroDeValidacao]
) -> None:
    if not isinstance(mes_obj, dict):
        erros.append(ErroDeValidacao(caminho, "mês deve ser um objeto"))
        return

    mes: int | None = None
    if "mes" not in mes_obj:
        erros.append(ErroDeValidacao(_junta(caminho, "mes"), "campo obrigatório 'mes' ausente"))
    elif not _inteiro(mes_obj["mes"]) or not 1 <= mes_obj["mes"] <= 12:
        erros.append(
            ErroDeValidacao(_junta(caminho, "mes"), "mes deve ser um inteiro entre 1 e 12")
        )
    else:
        mes = mes_obj["mes"]

    _validar_numero(mes_obj, "salario", caminho, erros)
    _validar_numero(mes_obj, "meta_investimento", caminho, erros)

    for campo, investimento in (
        ("receitas", False),
        ("despesas", False),
        ("investimentos", True),
    ):
        if campo not in mes_obj:
            continue
        lista = mes_obj[campo]
        caminho_lista = _junta(caminho, campo)
        if not isinstance(lista, list):
            erros.append(ErroDeValidacao(caminho_lista, f"{campo} deve ser uma lista"))
            continue
        for i, item in enumerate(lista):
            _validar_lancamento(item, f"{caminho_lista}[{i}]", investimento, ano, mes, erros)


def _validar_ano(ano_obj: object, caminho: str, erros: list[ErroDeValidacao]) -> None:
    if not isinstance(ano_obj, dict):
        erros.append(ErroDeValidacao(caminho, "ano deve ser um objeto"))
        return

    ano: int | None = None
    if "ano" not in ano_obj:
        erros.append(ErroDeValidacao(_junta(caminho, "ano"), "campo obrigatório 'ano' ausente"))
    elif not _inteiro(ano_obj["ano"]) or not 1 <= ano_obj["ano"] <= 9999:
        erros.append(
            ErroDeValidacao(_junta(caminho, "ano"), "ano deve ser um inteiro entre 1 e 9999")
        )
    else:
        ano = ano_obj["ano"]

    caminho_meses = _junta(caminho, "meses")
    if "meses" not in ano_obj:
        erros.append(ErroDeValidacao(caminho_meses, "campo obrigatório 'meses' ausente"))
    elif not isinstance(ano_obj["meses"], list):
        erros.append(ErroDeValidacao(caminho_meses, "meses deve ser uma lista"))
    else:
        for i, mes_obj in enumerate(ano_obj["meses"]):
            _validar_mes(mes_obj, f"{caminho_meses}[{i}]", ano, erros)


def validar(dados: object) -> list[ErroDeValidacao]:
    """Percorre todo o documento e devolve todos os erros. Lista vazia = válido."""
    erros: list[ErroDeValidacao] = []
    if not isinstance(dados, dict):
        return [ErroDeValidacao(_RAIZ, "o documento deve ser um objeto JSON")]

    if "moeda" in dados and not isinstance(dados["moeda"], str):
        erros.append(ErroDeValidacao("moeda", "moeda deve ser texto"))

    if "anos" not in dados:
        erros.append(ErroDeValidacao("anos", "campo obrigatório 'anos' ausente"))
    elif not isinstance(dados["anos"], list):
        erros.append(ErroDeValidacao("anos", "anos deve ser uma lista"))
    else:
        for i, ano_obj in enumerate(dados["anos"]):
            _validar_ano(ano_obj, f"anos[{i}]", erros)
    return erros
