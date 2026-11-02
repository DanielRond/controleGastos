"""Camada de serviço: as operações de aplicação, sem CLI, sem rede e sem interface.

É o único ponto que a CLI usa (e que uma futura API web usará) para carregar
dados, gerar a planilha e exportar CSV, em arquivo ou em memória.
"""

from __future__ import annotations

from pathlib import Path

from .exportador_csv import exportar_csv, exportar_csv_bytes
from .generator import gerar_planilha, gerar_planilha_bytes
from .loader import ErroDeValidacaoJSON, carregar_dados, carregar_json
from .modelo import LivroCaixa

__all__ = [
    "FORMATOS",
    "ErroDeValidacaoJSON",
    "carregar_arquivo",
    "carregar_dados",
    "exportar_csv_em_memoria",
    "gerar_arquivos",
    "gerar_planilha_em_memoria",
]

FORMATOS = ("xlsx", "csv", "ambos")


def carregar_arquivo(caminho: str | Path) -> LivroCaixa:
    """Lê o JSON, valida e constrói o livro-caixa (levanta ErroDeValidacaoJSON com todos os erros)."""
    return carregar_json(caminho)


def gerar_arquivos(livros: LivroCaixa, destino: str | Path, formato: str) -> list[Path]:
    """Grava os arquivos do formato pedido e devolve os caminhos: planilha primeiro, depois os CSV."""
    if formato not in FORMATOS:
        raise ValueError(f"formato inválido: {formato!r}; use um de: {', '.join(FORMATOS)}")
    gerados: list[Path] = []
    if formato in ("xlsx", "ambos"):
        gerados.append(gerar_planilha(livros, destino))
    if formato in ("csv", "ambos"):
        gerados.extend(exportar_csv(livros, destino))
    return gerados


def gerar_planilha_em_memoria(livros: LivroCaixa) -> bytes:
    """O .xlsx como bytes, sem tocar o disco."""
    return gerar_planilha_bytes(livros)


def exportar_csv_em_memoria(livros: LivroCaixa) -> tuple[bytes, bytes]:
    """Os CSV de lançamentos e de resumo mensal como bytes, sem tocar o disco."""
    return exportar_csv_bytes(livros)
