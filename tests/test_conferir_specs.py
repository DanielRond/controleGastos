"""Rastreabilidade entre specs vigentes e testes (scripts/conferir_specs.py)."""

import importlib.util
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("conferir", RAIZ / "scripts" / "conferir_specs.py")
conferir = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(conferir)


def test_todo_requisito_vigente_tem_teste_e_nenhum_id_e_inventado() -> None:
    assert conferir.problemas() == []


def test_detecta_requisito_sem_teste_e_id_inexistente(monkeypatch) -> None:
    monkeypatch.setattr(conferir, "ids_citados", lambda: {"VAL-01", "ZZZ-99"})
    erros = "\n".join(conferir.problemas())
    assert "VAL-02: requisito vigente sem teste" in erros
    assert "ZZZ-99: citado em teste, mas não existe" in erros
    assert "VAL-01: requisito vigente sem teste" not in erros


def test_spec_em_rascunho_nao_exige_teste() -> None:
    vigentes, definidos = conferir.ids_definidos()
    assert "WEB-01" in vigentes  # spec api: vigente
    assert "WEB-14" in definidos  # spec interface-web: rascunho
    assert "WEB-14" not in vigentes


def test_citacoes_em_testes_typescript_tambem_contam(tmp_path, monkeypatch) -> None:
    (tmp_path / "tests").mkdir()
    (tmp_path / "frontend" / "src" / "paginas").mkdir(parents=True)
    (tmp_path / "frontend" / "e2e").mkdir()
    (tmp_path / "frontend" / "node_modules" / "x").mkdir(parents=True)
    (tmp_path / "frontend" / "src" / "paginas" / "Login.test.tsx").write_text(
        "// Spec: WEB-20, WEB-21\nit('x', () => {})\n", encoding="utf-8"
    )
    (tmp_path / "frontend" / "e2e" / "fluxo.spec.ts").write_text("  // Spec: WEB-22\n", encoding="utf-8")
    (tmp_path / "frontend" / "node_modules" / "x" / "lixo.test.ts").write_text("// Spec: ZZZ-01\n", encoding="utf-8")
    (tmp_path / "tests" / "test_a.py").write_text("# Spec: VAL-01\n", encoding="utf-8")
    monkeypatch.setattr(conferir, "RAIZ", tmp_path)

    assert conferir.ids_citados() == {"VAL-01", "WEB-20", "WEB-21", "WEB-22"}
