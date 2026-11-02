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


def test_arquivos_typescript_do_frontend_sao_identificados() -> None:
    assert checar.classificar({"tool_input": {"file_path": "/x/frontend/src/paginas/Mes.tsx"}}) == (
        "ts",
        "frontend/src/paginas/Mes.tsx",
    )
    assert checar.classificar({"file_path": "C:\\proj\\frontend\\e2e\\fluxo.spec.ts"}) == ("ts", "frontend/e2e/fluxo.spec.ts")
    assert checar.classificar({"file_path": "/x/frontend/src/api/schema.d.ts"})[0] == "ignorar"  # gerado
    assert checar.classificar({"file_path": "/x/frontend/node_modules/a/b.ts"})[0] == "ignorar"
    assert checar.classificar({"file_path": "/x/frontend/src/estilo.css"})[0] == "ignorar"


def test_comandos_do_frontend_rodam_lint_tipos_e_testes_relacionados() -> None:
    comandos = checar.comandos_do_frontend("frontend/src/paginas/Mes.tsx")

    assert [argv for argv, _ in comandos] == [
        ["npm", "run", "lint"],
        ["npm", "run", "typecheck"],
        ["npx", "vitest", "related", "--run", "src/paginas/Mes.tsx"],
    ]
    assert all(cwd == checar.RAIZ / "frontend" for _, cwd in comandos)


def test_outros_arquivos_e_entrada_invalida_sao_ignorados() -> None:
    assert checar.classificar({"tool_input": {"file_path": "/x/README.md"}})[0] == "ignorar"
    assert checar.classificar({"cwd": "/x/y", "transcript_path": "/z/s.jsonl"})[0] == "ignorar"
    assert checar.classificar(None)[0] == "ignorar"


def test_alvos_de_teste_mapeiam_modulo_para_seus_testes() -> None:
    alvos = [Path(a).name for a in checar.alvos_de_teste("src/controlegastos/validador.py")]
    assert alvos == ["test_validador.py", "test_validador_propriedades.py"]
    assert [Path(a).name for a in checar.alvos_de_teste("tests/test_cli.py")] == ["test_cli.py"]
