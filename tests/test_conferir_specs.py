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
