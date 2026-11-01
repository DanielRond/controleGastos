import calendar
import copy

from hypothesis import given, settings
from hypothesis import strategies as st

from controlegastos.validador import TIPOS_DE_INVESTIMENTO_CONHECIDOS, validar

_texto = st.text(max_size=8)
_valor = st.floats(min_value=0, max_value=1_000_000, allow_nan=False, allow_infinity=False)
_numero = st.one_of(st.integers(min_value=0, max_value=100_000), _valor)


@st.composite
def _lancamento(draw, ano: int, mes: int, investimento: bool):
    item = {
        "descricao": draw(_texto),
        "valor": draw(_numero),
        "dia": draw(st.integers(1, calendar.monthrange(ano, mes)[1])),
    }
    if investimento:
        item["tipo"] = draw(st.sampled_from(sorted(TIPOS_DE_INVESTIMENTO_CONHECIDOS)))
        if draw(st.booleans()):
            item["ativo"] = draw(_texto)
    if draw(st.booleans()):
        item["categoria"] = draw(_texto)
    return item


@st.composite
def _mes(draw, ano: int, numero: int):
    mes = {"mes": numero}
    if draw(st.booleans()):
        mes["salario"] = draw(_numero)
    if draw(st.booleans()):
        mes["meta_investimento"] = draw(_numero)
    for campo, inv in (("receitas", False), ("despesas", False), ("investimentos", True)):
        if draw(st.booleans()):
            mes[campo] = draw(st.lists(_lancamento(ano, numero, inv), max_size=2))
    return mes


@st.composite
def documentos_validos(draw):
    anos = []
    for ano in draw(st.lists(st.integers(1, 9999), min_size=1, max_size=2, unique=True)):
        numeros = draw(st.lists(st.integers(1, 12), min_size=1, max_size=3, unique=True))
        meses = [draw(_mes(ano, n)) for n in numeros]
        anos.append({"ano": ano, "meses": meses})
    doc = {"anos": anos}
    if draw(st.booleans()):
        doc["moeda"] = draw(_texto)
    return doc


def _posicoes(doc: dict) -> list[tuple[str, dict, str]]:
    """Lista (caminho_do_lancamento_ou_mes, objeto, tipo) de objetos alcançáveis."""
    saida = []
    for i, ano in enumerate(doc["anos"]):
        for j, mes in enumerate(ano["meses"]):
            base = f"anos[{i}].meses[{j}]"
            saida.append((base, mes, "mes"))
            for campo in ("receitas", "despesas", "investimentos"):
                for k, item in enumerate(mes.get(campo, [])):
                    saida.append((f"{base}.{campo}[{k}]", item, campo))
    return saida


def _violacoes(doc: dict) -> list:
    """Cada violação é (caminho_esperado, função que injeta no documento)."""
    violacoes = []
    for i, ano in enumerate(doc["anos"]):
        violacoes.append((f"anos[{i}].meses", lambda d, i=i: d["anos"][i].pop("meses")))
        violacoes.append((f"anos[{i}].ano", lambda d, i=i: d["anos"][i].pop("ano")))
    for caminho, obj, tipo in _posicoes(doc):
        def alvo(d, caminho=caminho):
            atual = d
            for parte in _partes(caminho):
                atual = atual[parte]
            return atual

        if tipo == "mes":
            violacoes.append((f"{caminho}.mes", lambda d, a=alvo: a(d).update(mes=13)))
            violacoes.append((f"{caminho}.mes", lambda d, a=alvo: a(d).update(mes=0)))
            violacoes.append((f"{caminho}.salario", lambda d, a=alvo: a(d).update(salario=True)))
            violacoes.append(
                (f"{caminho}.meta_investimento", lambda d, a=alvo: a(d).update(meta_investimento="1"))
            )
            continue
        for campo in ("descricao", "valor", "dia"):
            violacoes.append((f"{caminho}.{campo}", lambda d, a=alvo, c=campo: a(d).pop(c)))
        violacoes.append((f"{caminho}.valor", lambda d, a=alvo: a(d).update(valor=True)))
        violacoes.append((f"{caminho}.valor", lambda d, a=alvo: a(d).update(valor="1")))
        violacoes.append((f"{caminho}.dia", lambda d, a=alvo: a(d).update(dia=32)))
        if tipo == "investimentos":
            violacoes.append((f"{caminho}.tipo", lambda d, a=alvo: a(d).update(tipo="desconhecido")))
    return violacoes


def _partes(caminho: str) -> list:
    partes: list = []
    for trecho in caminho.split("."):
        nome, _, resto = trecho.partition("[")
        partes.append(nome)
        if resto:
            partes.append(int(resto.rstrip("]")))
    return partes


def _independentes(violacoes: list) -> list:
    """Mantém uma violação por caminho, para não haver conflito entre injeções."""
    vistos: dict[str, object] = {}
    for caminho, fn in violacoes:
        vistos.setdefault(caminho, fn)
    return list(vistos.items())


# Spec: VAL-09, VAL-12 (propriedade: Documentos válidos não geram erros)
@settings(max_examples=100)
@given(documentos_validos())
def test_propriedade_1_documentos_validos_sem_erros(doc):
    assert validar(doc) == []


# Spec: VAL-09 (propriedade: Uma violação injetada é reportada no caminho correto)
@settings(max_examples=100)
@given(st.data())
def test_propriedade_2_violacao_injetada_no_caminho_correto(data):
    doc = data.draw(documentos_validos())
    violacoes = _violacoes(doc)
    caminho, injetar = data.draw(st.sampled_from(violacoes))
    injetar(doc)
    erros = [e for e in validar(doc) if e.caminho == caminho]
    assert erros
    assert all(e.mensagem for e in erros)


# Spec: VAL-04
def test_propriedade_2_dia_29_fevereiro_nao_bissexto():
    doc = {
        "anos": [
            {
                "ano": 2023,
                "meses": [{"mes": 2, "despesas": [{"descricao": "x", "valor": 1, "dia": 29}]}],
            }
        ]
    }
    assert "anos[0].meses[0].despesas[0].dia" in [e.caminho for e in validar(doc)]


# Spec: VAL-09 (propriedade: Todos os erros são reportados em uma única execução)
@settings(max_examples=100)
@given(st.data())
def test_propriedade_3_todos_os_erros_em_uma_execucao(data):
    doc = data.draw(documentos_validos())
    candidatas = _independentes(_violacoes(doc))
    # Remove campos pais/filhos conflitantes: só injeta onde o caminho esperado
    # não fica dentro de outra violação (ex.: remover 'meses' elimina seus filhos).
    candidatas = [
        (c, fn)
        for c, fn in candidatas
        if not any(
            c != outro and c.startswith(outro.rsplit(".", 1)[0] + ".") and outro.endswith((".meses", ".ano"))
            for outro, _ in candidatas
        )
    ]
    # Evita violações que alteram 'mes' (invalidam o contexto do dia) ou removem 'ano'/'meses'.
    candidatas = [
        (c, fn) for c, fn in candidatas if not c.endswith((".mes", ".ano", ".meses"))
    ]
    if not candidatas:
        return
    k = data.draw(st.integers(1, min(3, len(candidatas))))
    escolhidas = data.draw(
        st.lists(st.sampled_from(candidatas), min_size=k, max_size=k, unique_by=lambda x: x[0])
    )
    alvo = copy.deepcopy(doc)
    for _, injetar in escolhidas:
        injetar(alvo)
    caminhos = {e.caminho for e in validar(alvo)}
    for caminho, _ in escolhidas:
        assert caminho in caminhos
