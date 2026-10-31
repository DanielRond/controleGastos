"""Testes da interface de linha de comando (cli.py)."""

import sys
from pathlib import Path

from controlegastos.cli import main

RAIZ = Path(__file__).resolve().parent.parent
EXEMPLO = RAIZ / "data" / "entradas" / "exemplo.json"


def test_main_entrada_valida(tmp_path: Path, monkeypatch) -> None:
    destino = tmp_path / "planilha-test.xlsx"
    monkeypatch.setattr(
        sys,
        "argv",
        ["controlegastos", "gerar", str(EXEMPLO), "-o", str(destino)],
    )

    assert main() == 0
    assert destino.exists()


def test_main_entrada_inexistente(tmp_path: Path, monkeypatch) -> None:
    destino = tmp_path / "planilha-test.xlsx"
    monkeypatch.setattr(
        sys,
        "argv",
        ["controlegastos", "gerar", str(tmp_path / "nao-existe.json"), "-o", str(destino)],
    )

    assert main() == 1
    assert not destino.exists()


def _rodar(monkeypatch, *argumentos: str) -> int:
    monkeypatch.setattr(sys, "argv", ["controlegastos", *argumentos])
    return main()


def _json_invalido(tmp_path: Path) -> Path:
    import json

    arquivo = tmp_path / "invalido.json"
    dados = {
        "anos": [
            {
                "ano": 2025,
                "meses": [
                    {"mes": 1, "despesas": [{"descricao": "x", "valor": True, "dia": 40}]}
                ],
            }
        ]
    }
    arquivo.write_text(json.dumps(dados), encoding="utf-8")
    return arquivo


def test_entrada_invalida_lista_todos_os_erros_e_retorna_1(tmp_path, monkeypatch, caplog) -> None:
    destino = tmp_path / "p.xlsx"
    codigo = _rodar(monkeypatch, "gerar", str(_json_invalido(tmp_path)), "-o", str(destino), "--formato", "ambos")

    assert codigo == 1
    assert "anos[0].meses[0].despesas[0].valor" in caplog.text
    assert "anos[0].meses[0].despesas[0].dia" in caplog.text
    assert not list(tmp_path.glob("p*"))


def test_formato_padrao_gera_so_xlsx(tmp_path, monkeypatch, capsys) -> None:
    destino = tmp_path / "p.xlsx"
    assert _rodar(monkeypatch, "gerar", str(EXEMPLO), "-o", str(destino)) == 0
    assert sorted(p.name for p in tmp_path.iterdir()) == ["p.xlsx"]
    assert "Planilha disponível em:" in capsys.readouterr().out


def test_formato_csv_gera_dois_csv(tmp_path, monkeypatch, capsys) -> None:
    destino = tmp_path / "p.xlsx"
    assert _rodar(monkeypatch, "gerar", str(EXEMPLO), "-o", str(destino), "--formato", "csv") == 0
    assert sorted(p.name for p in tmp_path.iterdir()) == [
        "p-lancamentos.csv",
        "p-resumo-mensal.csv",
    ]
    assert capsys.readouterr().out.count("Arquivo disponível em:") == 2


def test_formato_ambos_informa_tres_caminhos(tmp_path, monkeypatch, capsys) -> None:
    destino = tmp_path / "p.xlsx"
    assert _rodar(monkeypatch, "gerar", str(EXEMPLO), "-o", str(destino), "--formato", "ambos") == 0
    assert sorted(p.name for p in tmp_path.iterdir()) == [
        "p-lancamentos.csv",
        "p-resumo-mensal.csv",
        "p.xlsx",
    ]
    assert capsys.readouterr().out.count("Arquivo disponível em:") == 3


def test_formato_invalido_mensagem_em_portugues(tmp_path, monkeypatch, capsys) -> None:
    import pytest

    with pytest.raises(SystemExit) as info:
        _rodar(monkeypatch, "gerar", str(EXEMPLO), "-o", str(tmp_path / "p.xlsx"), "--formato", "pdf")
    assert info.value.code != 0
    assert "Valor inválido para --formato" in capsys.readouterr().err


def test_ui_sem_streamlit_orienta_instalacao(monkeypatch, capsys) -> None:
    import importlib.util

    original = importlib.util.find_spec
    monkeypatch.setattr(
        importlib.util,
        "find_spec",
        lambda nome, *a, **k: None if nome == "streamlit" else original(nome, *a, **k),
    )
    assert _rodar(monkeypatch, "ui") != 0
    assert "uv sync --extra ui" in capsys.readouterr().err
