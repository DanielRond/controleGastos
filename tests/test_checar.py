"""Testes do script de checagem pós-edição (scripts/checar.py)."""

import importlib.util
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("checar", RAIZ / "scripts" / "checar.py")
checar = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(checar)


def test_py_em_src_e_identificado_em_formatos_diferentes() -> None:
    kiro = {"file_path": "/x/y/src/controlegastos/validador.py", "cwd": "/x/y"}
    claude = {"tool_input": {"file_path": "C:\\proj\\src\\controlegastos\\cli.py"}, "cwd": "C:\\proj"}
    assert checar.classificar(kiro) == ("py", "src/controlegastos/validador.py")
    assert checar.classificar(claude) == ("py", "src/controlegastos/cli.py")


def test_exemplo_json_dispara_a_suite_completa() -> None:
    evento = {"tool_input": {"file_path": "/x/data/entradas/exemplo.json"}}
    assert checar.classificar(evento) == ("esquema", None)


def test_outros_arquivos_e_entrada_invalida_sao_ignorados() -> None:
    assert checar.classificar({"tool_input": {"file_path": "/x/README.md"}})[0] == "ignorar"
    assert checar.classificar({"cwd": "/x/y", "transcript_path": "/z/s.jsonl"})[0] == "ignorar"
    assert checar.classificar(None)[0] == "ignorar"


def test_alvos_de_teste_mapeiam_modulo_para_seus_testes() -> None:
    alvos = [Path(a).name for a in checar.alvos_de_teste("src/controlegastos/validador.py")]
    assert alvos == ["test_validador.py", "test_validador_propriedades.py"]
    assert [Path(a).name for a in checar.alvos_de_teste("tests/test_cli.py")] == ["test_cli.py"]
