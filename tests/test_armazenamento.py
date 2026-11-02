"""Armazenamento em banco (armazenamento/): repositório, lixeira, importação e migrações."""

import ast
import copy
import json
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pytest

pytest.importorskip("sqlalchemy")

import sqlalchemy as sa
from controlegastos.armazenamento import (
    LancamentoInexistente,
    MesJaExiste,
    Repositorio,
    atualizar_banco,
    criar_engine,
    criar_sessao,
    criar_usuario,
    url_do_banco,
)

from controlegastos.exportador_csv import exportar_csv_bytes
from controlegastos.generator import gerar_planilha_bytes
from controlegastos.loader import (
    ErroDeValidacaoJSON,
    carregar_dados,
    carregar_json,
)
from controlegastos.validador import validar

RAIZ = Path(__file__).resolve().parent.parent
EXEMPLO = RAIZ / "data" / "entradas" / "exemplo.json"
COMPLETO = RAIZ / "data" / "entradas" / "exemplo-completo.json"


def _documento(caminho: Path = EXEMPLO) -> dict:
    return json.loads(caminho.read_text(encoding="utf-8"))


def _itens(doc: dict) -> int:
    return sum(
        len(mes.get(lista, []))
        for ano in doc["anos"]
        for mes in ano["meses"]
        for lista in ("receitas", "despesas", "investimentos")
    )


def _tres_lancamentos(repo: Repositorio) -> list[int]:
    return [
        repo.adicionar_lancamento(2025, 1, "receita", "Freela", Decimal("250.00"), 15, categoria="extra"),
        repo.adicionar_lancamento(2025, 1, "despesa", "Mercado", Decimal("100.50"), 3, categoria="alimentacao"),
        repo.adicionar_lancamento(
            2025, 1, "investimento", "Aporte", Decimal("80.00"), 10, tipo_investimento="renda_fixa", ativo="CDI"
        ),
    ]


# ---------------------------------------------------------------- STO-01


# Spec: STO-01
def test_url_vem_de_database_url_e_o_padrao_e_um_sqlite_local(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'x.db'}")
    assert url_do_banco() == f"sqlite:///{tmp_path / 'x.db'}"

    monkeypatch.delenv("DATABASE_URL")
    monkeypatch.setenv("CONTROLEGASTOS_DADOS", str(tmp_path / "dados"))
    assert url_do_banco() == f"sqlite:///{tmp_path / 'dados' / 'controlegastos.db'}"
    assert url_do_banco("sqlite://") == "sqlite://"  # argumento explícito vence


# Spec: STO-01
def test_cria_a_pasta_do_sqlite_local_ao_migrar(tmp_path) -> None:
    arquivo = tmp_path / "a" / "b" / "c.db"
    atualizar_banco(f"sqlite:///{arquivo}")
    assert arquivo.exists()


# Spec: STO-01
def test_dominio_e_saidas_nao_conhecem_o_banco() -> None:
    for nome in ("modelo", "loader", "validador", "generator", "exportador_csv", "resumo"):
        arvore = ast.parse((RAIZ / "src" / "controlegastos" / f"{nome}.py").read_text(encoding="utf-8"))
        importados = {
            (no.module or "").split(".")[0] if isinstance(no, ast.ImportFrom) else alias.name.split(".")[0]
            for no in ast.walk(arvore)
            for alias in (no.names if isinstance(no, (ast.Import, ast.ImportFrom)) else [])
        }
        assert "sqlalchemy" not in importados, nome


# ---------------------------------------------------------------- STO-02


# Spec: STO-02
def test_valores_ficam_em_centavos_inteiros_e_voltam_como_decimal(engine, repo) -> None:
    repo.adicionar_lancamento(2025, 1, "despesa", "x", Decimal("12.34"), 5)

    coluna = next(c for c in sa.inspect(engine).get_columns("lancamento") if c["name"] == "valor_centavos")
    assert "INT" in str(coluna["type"]).upper()
    with engine.connect() as conexao:
        bruto, tipo_sql = conexao.execute(sa.text("select valor_centavos, typeof(valor_centavos) from lancamento")).one()
    assert (bruto, tipo_sql) == (1234, "integer")

    lido = repo.listar_mes(2025, 1)[0].valor
    assert lido == Decimal("12.34")
    assert isinstance(lido, Decimal)


# ---------------------------------------------------------------- STO-03


# Spec: STO-03
def test_lancamento_tem_id_estavel_gerado_pelo_sistema_e_dono(engine, repo) -> None:
    id1, id2, _ = _tres_lancamentos(repo)
    assert isinstance(id1, int)
    assert id1 != id2

    repo.editar_lancamento(id1, descricao="Freela novo", valor=Decimal("260.00"))
    repo.apagar_lancamento(id1)
    repo.restaurar(id1)

    atual = next(item for item in repo.listar_mes(2025, 1) if item.id == id1)
    assert (atual.descricao, atual.valor) == ("Freela novo", Decimal("260.00"))
    with engine.connect() as conexao:
        donos = {linha[0] for linha in conexao.execute(sa.text("select usuario_id from lancamento"))}
    assert donos == {repo.usuario_id}


# Spec: STO-03
def test_mes_e_unico_por_usuario_ano_e_mes(engine, repo, repo_outro) -> None:
    repo.definir_mes(2025, 1, salario=Decimal("100.00"))
    repo.definir_mes(2025, 1, salario=Decimal("200.00"), meta_investimento=Decimal("50.00"))
    repo_outro.definir_mes(2025, 1, salario=Decimal("300.00"))

    with engine.connect() as conexao:
        linhas = conexao.execute(sa.text("select usuario_id, ano, mes, salario_centavos from mes order by usuario_id")).all()
    assert linhas == [(repo.usuario_id, 2025, 1, 20000), (repo_outro.usuario_id, 2025, 1, 30000)]


# Spec: STO-03
def test_nome_de_usuario_e_unico(sessao) -> None:
    criar_usuario(sessao, "ana", "h1")
    with pytest.raises(ValueError, match="já existe"):
        criar_usuario(sessao, "ana", "h2")


# ---------------------------------------------------------------- STO-04


# Spec: STO-04
def test_origem_padrao_e_manual_e_a_importacao_marca_importado_json(engine, repo) -> None:
    repo.adicionar_lancamento(2025, 5, "despesa", "x", Decimal("1.00"), 1)
    repo.importar_documento(_documento())

    with engine.connect() as conexao:
        origens = dict(conexao.execute(sa.text("select origem, count(*) from lancamento group by origem")).all())
    assert origens["manual"] == 1
    assert origens["importado_json"] == _itens(_documento())


# Spec: STO-04
def test_origem_reservada_extrato_e_aceita_e_outras_sao_recusadas(repo) -> None:
    repo.adicionar_lancamento(2025, 1, "despesa", "x", Decimal("1.00"), 1, origem="extrato")
    with pytest.raises(ValueError, match="origem"):
        repo.adicionar_lancamento(2025, 1, "despesa", "x", Decimal("1.00"), 1, origem="outra")


# ---------------------------------------------------------------- STO-05


# Spec: STO-05
def test_importacao_com_falha_no_meio_nao_deixa_dados_parciais(repo, monkeypatch) -> None:
    original = Repositorio._inserir_lancamento
    chamadas = {"n": 0}

    def falha_na_terceira(self, *args, **kwargs):
        chamadas["n"] += 1
        if chamadas["n"] == 3:
            raise RuntimeError("falha simulada")
        return original(self, *args, **kwargs)

    monkeypatch.setattr(Repositorio, "_inserir_lancamento", falha_na_terceira)
    with pytest.raises(RuntimeError, match="simulada"):
        repo.importar_documento(_documento())
    monkeypatch.undo()

    assert repo.carregar_livro().anos == {}
    assert repo.listar_lixeira() == []


# Spec: STO-05
def test_lancamento_invalido_nao_grava_nada(repo) -> None:
    with pytest.raises(ErroDeValidacaoJSON):
        repo.adicionar_lancamento(2025, 2, "despesa", "x", Decimal("1.00"), 31)  # fevereiro não tem dia 31
    assert repo.listar_mes(2025, 2) == []


# ---------------------------------------------------------------- STO-06


# Spec: STO-06
def test_um_usuario_nao_ve_nem_altera_dados_de_outro(repo, repo_outro) -> None:
    id_a = _tres_lancamentos(repo)[0]
    repo.definir_mes(2025, 1, salario=Decimal("1000.00"))

    assert repo_outro.listar_mes(2025, 1) == []
    assert repo_outro.carregar_livro().anos == {}
    assert repo_outro.exportar_documento()["anos"] == []

    for acao in (
        lambda: repo_outro.editar_lancamento(id_a, descricao="invadido"),
        lambda: repo_outro.apagar_lancamento(id_a),
    ):
        with pytest.raises(LancamentoInexistente):
            acao()

    repo.apagar_lancamento(id_a)
    assert repo_outro.listar_lixeira() == []
    for acao in (lambda: repo_outro.restaurar(id_a), lambda: repo_outro.excluir_definitivamente(id_a)):
        with pytest.raises(LancamentoInexistente):
            acao()
    assert repo_outro.esvaziar_lixeira() == 0
    assert [item.id for item in repo.listar_lixeira()] == [id_a]


# Spec: STO-06
def test_mes_existente_de_outro_usuario_nao_bloqueia_a_importacao(repo, repo_outro) -> None:
    repo.importar_documento(_documento())
    resultado = repo_outro.importar_documento(_documento())  # mesmos meses, outro dono: sem conflito
    assert resultado.lancamentos_criados == _itens(_documento())


# ---------------------------------------------------------------- STO-07


# Spec: STO-07
def test_migracao_cria_o_esquema_e_e_idempotente_sem_perder_dados(tmp_path) -> None:
    url = f"sqlite:///{tmp_path / 'banco.db'}"
    atualizar_banco(url)
    motor = criar_engine(url)
    with criar_sessao(motor) as sessao:
        criar_usuario(sessao, "ana", "hash")

    atualizar_banco(url)  # segunda vez: nada muda, nada se perde

    with motor.connect() as conexao:
        assert conexao.execute(sa.text("select nome from usuario")).scalar_one() == "ana"
        assert conexao.execute(sa.text("select count(*) from alembic_version")).scalar_one() == 1
    assert {"usuario", "mes", "lancamento"} <= set(sa.inspect(motor).get_table_names())
    motor.dispose()


# Spec: STO-07
def test_esquema_migrado_e_igual_aos_modelos(engine) -> None:
    from alembic.autogenerate import compare_metadata
    from alembic.migration import MigrationContext
    from controlegastos.armazenamento.modelos import Base

    with engine.connect() as conexao:
        diferencas = compare_metadata(MigrationContext.configure(conexao), Base.metadata)
    assert diferencas == []


# ---------------------------------------------------------------- STO-08


# Spec: STO-08
def test_importa_o_exemplo_e_informa_o_que_criou(repo) -> None:
    doc = _documento()
    resultado = repo.importar_documento(doc)

    assert resultado.lancamentos_criados == _itens(doc)
    assert resultado.meses == [(2025, 1), (2025, 2)]
    assert resultado.substituidos == 0


# Spec: STO-08
def test_importacao_invalida_nao_grava_e_devolve_todos_os_erros(repo) -> None:
    doc = _documento()
    doc["anos"][0]["meses"][0]["despesas"][0]["dia"] = 40
    doc["anos"][0]["meses"][1]["mes"] = 13

    with pytest.raises(ErroDeValidacaoJSON) as info:
        repo.importar_documento(doc)

    assert len(info.value.erros) == 2
    assert repo.carregar_livro().anos == {}


# Spec: STO-08
def test_importacao_recusa_mes_que_ja_existe_e_nao_altera_nada(repo) -> None:
    repo.importar_documento(_documento())
    antes = repo.exportar_documento()

    with pytest.raises(MesJaExiste) as info:
        repo.importar_documento(_documento())

    assert info.value.meses == [(2025, 1), (2025, 2)]
    assert repo.exportar_documento() == antes


# Spec: STO-08
def test_mes_so_com_salario_ou_meta_conta_como_existente(repo) -> None:
    repo.definir_mes(2025, 2, meta_investimento=Decimal("10.00"))
    with pytest.raises(MesJaExiste) as info:
        repo.importar_documento(_documento())
    assert info.value.meses == [(2025, 2)]


# Spec: STO-08
def test_substituir_troca_os_meses_do_arquivo_e_preserva_os_demais(repo) -> None:
    repo.importar_documento(_documento())
    repo.adicionar_lancamento(2025, 3, "despesa", "Março", Decimal("7.00"), 2)
    fevereiro_antes = copy.deepcopy(repo.carregar_livro().ano(2025).mes(2))
    antigos_janeiro = len(repo.listar_mes(2025, 1))

    novo = {
        "anos": [{"ano": 2025, "meses": [{"mes": 1, "salario": 10, "despesas": [{"descricao": "Só esta", "valor": 1.5, "dia": 2}]}]}]
    }
    resultado = repo.importar_documento(novo, substituir=True)

    livro = repo.carregar_livro()
    janeiro = livro.ano(2025).mes(1)
    assert [d.descricao for d in janeiro.despesas] == ["Só esta"]
    assert janeiro.total_receitas == Decimal(10)
    assert livro.ano(2025).mes(2) == fevereiro_antes
    assert [d.descricao for d in livro.ano(2025).mes(3).despesas] == ["Março"]
    assert resultado.substituidos == antigos_janeiro
    assert len(repo.listar_lixeira()) == antigos_janeiro  # os antigos de janeiro foram para a lixeira


# ---------------------------------------------------------------- STO-09


# Spec: STO-09
@pytest.mark.parametrize("caminho", [EXEMPLO, COMPLETO])
def test_exportar_json_faz_ida_e_volta_com_o_mesmo_livro(repo, caminho) -> None:
    repo.importar_documento(_documento(caminho))
    exportado = repo.exportar_documento()

    assert validar(exportado) == []
    assert carregar_dados(json.loads(json.dumps(exportado))) == carregar_json(caminho)


# Spec: STO-09
def test_exportar_ignora_a_lixeira(repo) -> None:
    ids = _tres_lancamentos(repo)
    repo.apagar_lancamento(ids[1])

    despesas = repo.exportar_documento()["anos"][0]["meses"][0]["despesas"]
    assert despesas == []


# ---------------------------------------------------------------- STO-10


# Spec: STO-10
@pytest.mark.parametrize("caminho", [EXEMPLO, COMPLETO])
def test_carregar_do_banco_equivale_a_carregar_o_json(repo, caminho) -> None:
    repo.importar_documento(_documento(caminho))
    assert repo.carregar_livro() == carregar_json(caminho)


# Spec: STO-10
def test_valores_de_referencia_do_exemplo_vindos_do_banco(repo) -> None:
    repo.importar_documento(_documento())
    janeiro = repo.carregar_livro().ano(2025).mes(1)

    assert janeiro.total_receitas == Decimal("5250.00")
    assert janeiro.total_despesas == Decimal("1780.00")
    assert janeiro.total_investimentos == Decimal("1000.00")
    assert janeiro.saldo_livre == Decimal("2470.00")
    assert janeiro.meta_investimento == Decimal("1000.00")


# ---------------------------------------------------------------- STO-11


# Spec: STO-11
def test_valor_com_mais_de_duas_casas_e_rejeitado_no_campo_e_nada_e_gravado(repo) -> None:
    with pytest.raises(ErroDeValidacaoJSON) as info:
        repo.adicionar_lancamento(2025, 1, "despesa", "x", Decimal("10.123"), 5)

    assert [(e.caminho, e.mensagem) for e in info.value.erros] == [("valor", "valor deve ter no máximo 2 casas decimais")]
    assert repo.listar_mes(2025, 1) == []


# Spec: STO-11
def test_importacao_rejeita_mais_de_duas_casas_no_caminho_do_documento(repo) -> None:
    doc = _documento()
    doc["anos"][0]["meses"][0]["despesas"][0]["valor"] = 10.123

    with pytest.raises(ErroDeValidacaoJSON) as info:
        repo.importar_documento(doc)

    assert [e.caminho for e in info.value.erros] == ["anos[0].meses[0].despesas[0].valor"]
    assert repo.carregar_livro().anos == {}


# Spec: STO-11
def test_salario_e_meta_do_mes_tambem_sao_validados(repo) -> None:
    with pytest.raises(ErroDeValidacaoJSON) as info:
        repo.definir_mes(2025, 1, salario=Decimal("1.001"), meta_investimento=Decimal("2.005"))
    assert sorted(e.caminho for e in info.value.erros) == ["meta_investimento", "salario"]


# ---------------------------------------------------------------- STO-12


# Spec: STO-12
def test_apagar_envia_para_a_lixeira_e_some_de_todas_as_leituras(engine, repo) -> None:
    receita, despesa, _ = _tres_lancamentos(repo)
    repo.apagar_lancamento(despesa)

    assert [item.id for item in repo.listar_mes(2025, 1)] != []
    assert despesa not in [item.id for item in repo.listar_mes(2025, 1)]
    janeiro = repo.carregar_livro().ano(2025).mes(1)
    assert janeiro.total_despesas == Decimal(0)
    assert repo.exportar_documento()["anos"][0]["meses"][0]["despesas"] == []

    lixo = repo.listar_lixeira()
    assert [item.id for item in lixo] == [despesa]
    assert isinstance(lixo[0].apagado_em, datetime)
    with engine.connect() as conexao:  # a linha continua no banco: exclusão lógica
        assert conexao.execute(sa.text("select count(*) from lancamento where id = :i"), {"i": despesa}).scalar_one() == 1
    with pytest.raises(LancamentoInexistente):
        repo.apagar_lancamento(despesa)  # já está na lixeira
    assert receita in [item.id for item in repo.listar_mes(2025, 1)]


# Spec: STO-12
def test_planilha_e_csv_nunca_contem_item_da_lixeira(repo) -> None:
    _, despesa, _ = _tres_lancamentos(repo)
    repo.apagar_lancamento(despesa)
    livro = repo.carregar_livro()

    lancamentos, _ = exportar_csv_bytes(livro)
    assert b"Mercado" not in lancamentos
    assert b"Freela" in lancamentos
    assert gerar_planilha_bytes(livro).startswith(b"PK")


# Spec: STO-12
def test_item_da_lixeira_nao_pode_ser_editado(repo) -> None:
    id_ = _tres_lancamentos(repo)[0]
    repo.apagar_lancamento(id_)
    with pytest.raises(LancamentoInexistente):
        repo.editar_lancamento(id_, descricao="x")


# ---------------------------------------------------------------- STO-13


# Spec: STO-13
def test_restaurar_devolve_ao_mesmo_mes_com_o_mesmo_id_e_os_totais_originais(repo) -> None:
    ids = _tres_lancamentos(repo)
    antes = repo.carregar_livro()
    repo.apagar_lancamento(ids[1])
    repo.restaurar(ids[1])

    assert repo.carregar_livro() == antes
    assert repo.listar_lixeira() == []
    with pytest.raises(LancamentoInexistente):
        repo.restaurar(ids[1])  # não está mais na lixeira


# Spec: STO-13
def test_excluir_definitivamente_so_age_sobre_item_da_lixeira(engine, repo) -> None:
    ativo, apagado, _ = _tres_lancamentos(repo)
    repo.apagar_lancamento(apagado)

    with pytest.raises(LancamentoInexistente):
        repo.excluir_definitivamente(ativo)  # ativo não vai direto para o fim
    repo.excluir_definitivamente(apagado)

    with engine.connect() as conexao:
        restantes = {linha[0] for linha in conexao.execute(sa.text("select id from lancamento"))}
    assert apagado not in restantes
    assert ativo in restantes


# Spec: STO-13
def test_esvaziar_remove_so_os_apagados_do_dono_e_diz_quantos(engine, repo, repo_outro) -> None:
    ids = _tres_lancamentos(repo)
    do_outro = repo_outro.adicionar_lancamento(2025, 1, "despesa", "dele", Decimal("1.00"), 1)
    repo.apagar_lancamento(ids[0])
    repo.apagar_lancamento(ids[1])
    repo_outro.apagar_lancamento(do_outro)

    assert repo.esvaziar_lixeira() == 2
    assert repo.listar_lixeira() == []
    assert [item.id for item in repo_outro.listar_lixeira()] == [do_outro]
    assert [item.id for item in repo.listar_mes(2025, 1)] == [ids[2]]


# ---------------------------------------------------------------- STO-14


# Spec: STO-14
def test_lixeira_nao_expira_sozinha(engine, repo) -> None:
    id_ = _tres_lancamentos(repo)[0]
    repo.apagar_lancamento(id_)
    with engine.begin() as conexao:
        conexao.execute(sa.text("update lancamento set apagado_em = '2000-01-01 00:00:00' where id = :i"), {"i": id_})

    repo.adicionar_lancamento(2026, 1, "despesa", "novo", Decimal("1.00"), 1)  # outras operações não limpam nada
    repo.importar_documento({"anos": [{"ano": 2030, "meses": [{"mes": 1}]}]})
    repo.carregar_livro()
    repo.exportar_documento()

    assert [item.id for item in repo.listar_lixeira()] == [id_]
