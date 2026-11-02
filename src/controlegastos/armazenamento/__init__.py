"""Armazenamento em banco (SQLite por padrão): specs/armazenamento.

Exige o extra `web` (`uv sync --extra web`). O domínio e as saídas não importam este pacote.
"""

from .banco import (
    aplicar_migracoes,
    atualizar_banco,
    criar_engine,
    criar_sessao,
    url_do_banco,
)
from .centavos import de_centavos, para_centavos
from .repositorio import (
    LancamentoDados,
    LancamentoInexistente,
    MesJaExiste,
    Repositorio,
    ResultadoImportacao,
)
from .usuarios import criar_usuario

__all__ = [
    "LancamentoDados",
    "LancamentoInexistente",
    "MesJaExiste",
    "Repositorio",
    "ResultadoImportacao",
    "aplicar_migracoes",
    "atualizar_banco",
    "criar_engine",
    "criar_sessao",
    "criar_usuario",
    "de_centavos",
    "para_centavos",
    "url_do_banco",
]
