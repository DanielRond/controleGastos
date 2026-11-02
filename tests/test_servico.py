"""Camada de serviço (servico.py): orquestração usada pela CLI e, depois, pela web."""

import json
from pathlib import Path

import pytest

from controlegastos import servico
from controlegastos.loader import ErroDeValidacaoJSON

RAIZ = Path(__file__).resolve().parent.parent
EXEMPLO = RAIZ / "data" / "entradas" / "exemplo.json"


# Spec: LAN-07
def test_carrega_de_arquivo_e_de_dicionario_com_o_mesmo_resultado() -> None:
    do_arquivo = servico.carregar_arquivo(EXEMPLO)
    do_dicionario = servico.carregar_dados(json.loads(EXEMPLO.read_text(encoding="utf-8")))

    assert do_arquivo.ano(2025).mes(1).saldo_livre == do_dicionario.ano(2025).mes(1).saldo_livre


# Spec: LAN-07
def test_carregar_dados_invalidos_levanta_com_todos_os_erros() -> None:
    with pytest.raises(ErroDeValidacaoJSON) as info:
        servico.carregar_dados({"anos": [{"ano": 2025, "meses": [{"mes": 13}, {"mes": 0}]}]})

    assert len(info.value.erros) == 2


# Spec: LAN-07
def test_gerar_arquivos_conforme_o_formato(tmp_path: Path) -> None:
    livro = servico.carregar_arquivo(EXEMPLO)

    xlsx = servico.gerar_arquivos(livro, tmp_path / "a" / "p.xlsx", "xlsx")
    csv = servico.gerar_arquivos(livro, tmp_path / "b" / "p.xlsx", "csv")
    ambos = servico.gerar_arquivos(livro, tmp_path / "c" / "p.xlsx", "ambos")

    assert [p.name for p in xlsx] == ["p.xlsx"]
    assert [p.name for p in csv] == ["p-lancamentos.csv", "p-resumo-mensal.csv"]
    assert [p.name for p in ambos] == ["p.xlsx", "p-lancamentos.csv", "p-resumo-mensal.csv"]
    assert all(p.exists() for p in xlsx + csv + ambos)
    assert not (tmp_path / "b" / "p.xlsx").exists()  # csv não gera a planilha


# Spec: LAN-07
def test_formato_desconhecido_e_recusado_sem_gravar(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="formato"):
        servico.gerar_arquivos(servico.carregar_arquivo(EXEMPLO), tmp_path / "p.xlsx", "pdf")
    assert list(tmp_path.iterdir()) == []


# Spec: LAN-07
def test_em_memoria_devolve_bytes_equivalentes_aos_arquivos(tmp_path: Path) -> None:
    livro = servico.carregar_arquivo(EXEMPLO)
    gravados = servico.gerar_arquivos(livro, tmp_path / "p.xlsx", "ambos")

    xlsx = servico.gerar_planilha_em_memoria(livro)
    lancamentos, resumo = servico.exportar_csv_em_memoria(livro)

    assert xlsx.startswith(b"PK")
    assert lancamentos == gravados[1].read_bytes()
    assert resumo == gravados[2].read_bytes()


# Spec: LAN-07
def test_servico_nao_conhece_a_cli_nem_frameworks_web() -> None:
    codigo = (RAIZ / "src" / "controlegastos" / "servico.py").read_text(encoding="utf-8")
    for proibido in ("argparse", "from .cli", "import cli", "fastapi", "sqlalchemy", "print("):
        assert proibido not in codigo, proibido
