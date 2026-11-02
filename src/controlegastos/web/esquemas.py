"""Corpos de entrada e saída da API. Dinheiro sempre como texto decimal (WEB-17)."""

from __future__ import annotations

import re
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    ValidationInfo,
    WithJsonSchema,
)

_TEXTO_DECIMAL = re.compile(r"^-?\d+(\.\d+)?$")
_SCHEMA_DINHEIRO = {"type": "string", "pattern": r"^-?\d+(\.\d+)?$", "examples": ["1200.00"]}


def texto_dinheiro(valor: Decimal) -> str:
    """Decimal em texto com duas casas: 12.5 -> '12.50'."""
    return format(valor.quantize(Decimal("0.01")), "f")


def _para_decimal(valor: object, info: ValidationInfo) -> Decimal:
    if not isinstance(valor, str) or not _TEXTO_DECIMAL.match(valor):
        raise ValueError(f'{info.field_name} deve ser um texto decimal, ex.: "12.34"')
    return Decimal(valor)


def _para_decimal_ou_nulo(valor: object, info: ValidationInfo) -> Decimal | None:
    return None if valor is None else _para_decimal(valor, info)


Dinheiro = Annotated[Decimal, BeforeValidator(_para_decimal), WithJsonSchema(_SCHEMA_DINHEIRO)]
DinheiroOuNulo = Annotated[
    Decimal | None,
    BeforeValidator(_para_decimal_ou_nulo),
    WithJsonSchema({**_SCHEMA_DINHEIRO, "type": ["string", "null"]}),
]
Inteiro = Annotated[int, Field(strict=True)]
Tipo = Literal["receita", "despesa", "investimento"]


class Entrada(BaseModel):
    model_config = ConfigDict(extra="forbid")


class LoginEntrada(Entrada):
    nome: str
    senha: str


class LancamentoEntrada(Entrada):
    ano: Inteiro
    mes: Inteiro
    tipo: Tipo
    descricao: str
    valor: Dinheiro
    dia: Inteiro
    categoria: str | None = None
    tipo_investimento: str | None = None
    ativo: str | None = None


class LancamentoAtualizacao(Entrada):
    """Só os campos enviados mudam (`model_fields_set`)."""

    descricao: str = None  # type: ignore[assignment]
    valor: Dinheiro = None  # type: ignore[assignment]
    dia: Inteiro = None  # type: ignore[assignment]
    categoria: str | None = None
    tipo_investimento: str | None = None
    ativo: str | None = None


class MesEntrada(Entrada):
    """Só os campos enviados mudam; `null` limpa."""

    salario: DinheiroOuNulo = None
    meta_investimento: DinheiroOuNulo = None


class Usuario(BaseModel):
    id: int
    nome: str
    csrf_token: str


class Lancamento(BaseModel):
    id: int
    ano: int
    mes: int
    tipo: str
    descricao: str
    valor: str
    dia: int
    categoria: str
    tipo_investimento: str | None
    ativo: str | None
    origem: str
    apagado_em: str | None = None


class Totais(BaseModel):
    receitas: str
    despesas: str
    investimentos: str
    saldo_livre: str


class Classe(BaseModel):
    tipo: str
    total: str
    percentual: str


class Meta(BaseModel):
    valor: str
    investido: str
    diferenca: str
    situacao: Literal["falta", "acima"]


class MesSaida(BaseModel):
    ano: int
    mes: int
    salario: str | None
    meta_investimento: str | None
    lancamentos: list[Lancamento]
    totais: Totais
    investimentos_por_classe: list[Classe]
    meta: Meta | None


class ResumoMes(BaseModel):
    mes: int
    receitas: str
    despesas: str
    investimentos: str
    saldo_livre: str


class PontoSerie(BaseModel):
    rotulo: str
    valor: str


class ItemRanking(BaseModel):
    categoria: str
    total: str


class AnoSaida(BaseModel):
    ano: int
    meses: list[ResumoMes]
    patrimonio: list[PontoSerie]
    ranking: list[ItemRanking]
    variacao: list[PontoSerie]


class ErroCampo(BaseModel):
    caminho: str
    mensagem: str


class ErrosValidacao(BaseModel):
    erros: list[ErroCampo]


class Detalhe(BaseModel):
    detalhe: str


class MesRef(BaseModel):
    ano: int
    mes: int


class ResultadoImportacao(BaseModel):
    lancamentos_criados: int
    meses: list[MesRef]
    substituidos: int


class Conflito(BaseModel):
    mensagem: str
    meses: list[MesRef]


class Removidos(BaseModel):
    removidos: int
