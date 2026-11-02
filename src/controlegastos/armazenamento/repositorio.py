"""Repositório: único acesso aos dados de um usuário (STO-03 a STO-14).

Regras centrais:
- toda consulta passa por `_ativos()` ou `_apagados()`, que já filtram o dono (STO-06) e a
  lixeira (STO-12); não há leitura de `lancamento` fora delas;
- cada operação pública é uma transação: ou grava tudo ou nada (STO-05);
- dinheiro entra e sai como Decimal; no banco é inteiro em centavos (STO-02).
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from ..loader import ErroDeValidacaoJSON
from ..modelo import Despesa, Investimento, LivroCaixa, Receita
from ..validador import ErroDeValidacao, casas_decimais, validar
from .centavos import de_centavos, para_centavos
from .modelos import LancamentoRegistro, MesRegistro, agora

TIPOS = ("receita", "despesa", "investimento")
ORIGENS = ("manual", "importado_json", "extrato")
_LISTA_DO_TIPO = {"receita": "receitas", "despesa": "despesas", "investimento": "investimentos"}
_CAMPOS_EDITAVEIS = {"descricao", "valor", "dia", "categoria", "tipo_investimento", "ativo"}
_AUSENTE = object()
_PREFIXO_DO_DOCUMENTO = re.compile(r"^anos\[0\]\.(?:meses\[0\]\.)?(?:(?:receitas|despesas|investimentos)\[0\]\.?)?")


class LancamentoInexistente(LookupError):
    """O lançamento não existe, é de outro usuário ou não está no estado esperado."""


class MesJaExiste(ValueError):
    """A importação traz meses que já têm dados; use `substituir=True` para trocá-los."""

    def __init__(self, meses: list[tuple[int, int]]) -> None:
        self.meses = meses
        nomes = ", ".join(f"{ano}-{mes:02d}" for ano, mes in meses)
        super().__init__(f"já existem dados nos meses: {nomes}; use substituir para trocá-los")


@dataclass(frozen=True, slots=True)
class LancamentoDados:
    id: int
    ano: int
    mes: int
    tipo: str
    descricao: str
    valor: Decimal
    dia: int
    categoria: str
    tipo_investimento: str | None
    ativo: str | None
    origem: str
    apagado_em: datetime | None


@dataclass(frozen=True, slots=True)
class ResultadoImportacao:
    lancamentos_criados: int
    meses: list[tuple[int, int]]
    substituidos: int


def _numero_json(centavos: int) -> int | float:
    valor = de_centavos(centavos)
    return int(valor) if valor == valor.to_integral_value() else float(valor)


class Repositorio:
    def __init__(self, sessao: Session, usuario_id: int) -> None:
        self.sessao = sessao
        self.usuario_id = usuario_id

    # ------------------------------------------------------------ infraestrutura

    @contextmanager
    def _transacao(self) -> Iterator[None]:
        try:
            yield
            self.sessao.commit()
        except BaseException:
            self.sessao.rollback()
            raise

    def _ativos(self):
        """Única porta de leitura dos lançamentos vivos do dono (STO-06, STO-12)."""
        return select(LancamentoRegistro).where(
            LancamentoRegistro.usuario_id == self.usuario_id, LancamentoRegistro.apagado_em.is_(None)
        )

    def _apagados(self):
        """Única porta de leitura da lixeira do dono."""
        return select(LancamentoRegistro).where(
            LancamentoRegistro.usuario_id == self.usuario_id, LancamentoRegistro.apagado_em.is_not(None)
        )

    def _achar(self, consulta, id_: int) -> LancamentoRegistro:
        registro = self.sessao.scalars(consulta.where(LancamentoRegistro.id == id_)).first()
        if registro is None:
            raise LancamentoInexistente(id_)
        return registro

    def _mes(self, ano: int, mes: int, *, criar: bool) -> MesRegistro | None:
        registro = self.sessao.scalars(
            select(MesRegistro).where(
                MesRegistro.usuario_id == self.usuario_id, MesRegistro.ano == ano, MesRegistro.mes == mes
            )
        ).first()
        if registro is None and criar:
            registro = MesRegistro(usuario_id=self.usuario_id, ano=ano, mes=mes)
            self.sessao.add(registro)
            self.sessao.flush()
        return registro

    def _dados(self, registro: LancamentoRegistro, ano: int, mes: int) -> LancamentoDados:
        return LancamentoDados(
            id=registro.id,
            ano=ano,
            mes=mes,
            tipo=registro.tipo,
            descricao=registro.descricao,
            valor=de_centavos(registro.valor_centavos),
            dia=registro.dia,
            categoria=registro.categoria,
            tipo_investimento=registro.tipo_investimento,
            ativo=registro.ativo,
            origem=registro.origem,
            apagado_em=registro.apagado_em,
        )

    def _listar(self, consulta) -> list[LancamentoDados]:
        linhas = self.sessao.execute(
            consulta.add_columns(MesRegistro.ano, MesRegistro.mes)
            .join(MesRegistro, MesRegistro.id == LancamentoRegistro.mes_id)
            .order_by(MesRegistro.ano, MesRegistro.mes, LancamentoRegistro.id)
        ).all()
        return [self._dados(registro, ano, mes) for registro, ano, mes in linhas]

    # ------------------------------------------------------------ validação

    @staticmethod
    def _validar(ano: int, mes: int, tipo: str | None, item: dict | None, mes_extras: dict) -> None:
        """Reaproveita o validador do JSON (VAL-*); os caminhos voltam relativos ao campo."""
        dinheiro = {**mes_extras, **({"valor": item["valor"]} if item else {})}
        for campo, valor in dinheiro.items():
            if valor is not None and (isinstance(valor, bool) or not isinstance(valor, Decimal)):
                raise TypeError(f"{campo}: dinheiro deve ser Decimal, nunca float")

        estrutura = {k: float(v) for k, v in mes_extras.items() if v is not None}
        documento_mes: dict = {"mes": mes, **estrutura}
        if item is not None and tipo is not None:
            documento_mes[_LISTA_DO_TIPO[tipo]] = [{**item, "valor": float(item["valor"])}]
        erros = [
            ErroDeValidacao(_PREFIXO_DO_DOCUMENTO.sub("", e.caminho) or e.caminho, e.mensagem)
            for e in validar({"anos": [{"ano": ano, "meses": [documento_mes]}]})
        ]
        for campo, valor in dinheiro.items():
            if valor is not None and casas_decimais(valor) > 2:
                erros.append(ErroDeValidacao(campo, f"{campo} deve ter no máximo 2 casas decimais"))

        vistos: set[tuple[str, str]] = set()
        unicos = []
        for erro in erros:
            if (erro.caminho, erro.mensagem) not in vistos:
                vistos.add((erro.caminho, erro.mensagem))
                unicos.append(erro)
        if unicos:
            raise ErroDeValidacaoJSON(unicos)

    @staticmethod
    def _item(descricao, valor, dia, categoria, tipo, tipo_investimento, ativo) -> dict:
        item: dict = {"descricao": descricao, "valor": valor, "dia": dia, "categoria": categoria if categoria is not None else "geral"}
        if tipo == "investimento":
            if tipo_investimento is not None:
                item["tipo"] = tipo_investimento
            if ativo is not None:
                item["ativo"] = ativo
        return item

    # ------------------------------------------------------------ escrita

    def definir_mes(self, ano: int, mes: int, *, salario=_AUSENTE, meta_investimento=_AUSENTE) -> None:
        """Define salário e/ou meta do mês (None limpa o campo); o que não for passado não muda."""
        campos = {
            nome: valor
            for nome, valor in (("salario", salario), ("meta_investimento", meta_investimento))
            if valor is not _AUSENTE
        }
        self._validar(ano, mes, None, None, campos)
        with self._transacao():
            registro = self._mes(ano, mes, criar=True)
            if "salario" in campos:
                registro.salario_centavos = None if campos["salario"] is None else para_centavos(campos["salario"])
            if "meta_investimento" in campos:
                meta = campos["meta_investimento"]
                registro.meta_investimento_centavos = None if meta is None else para_centavos(meta)

    def _inserir_lancamento(
        self, mes: MesRegistro, tipo, descricao, centavos, dia, categoria, tipo_investimento, ativo, origem
    ) -> LancamentoRegistro:
        registro = LancamentoRegistro(
            usuario_id=self.usuario_id,
            mes_id=mes.id,
            tipo=tipo,
            descricao=descricao,
            valor_centavos=centavos,
            dia=dia,
            categoria=categoria if categoria is not None else "geral",
            tipo_investimento=tipo_investimento if tipo == "investimento" else None,
            ativo=ativo if tipo == "investimento" else None,
            origem=origem,
        )
        self.sessao.add(registro)
        return registro

    def adicionar_lancamento(
        self,
        ano: int,
        mes: int,
        tipo: str,
        descricao: str,
        valor: Decimal,
        dia: int,
        *,
        categoria: str = "geral",
        tipo_investimento: str | None = None,
        ativo: str | None = None,
        origem: str = "manual",
    ) -> int:
        if tipo not in TIPOS:
            raise ValueError(f"tipo inválido: {tipo!r}; use um de: {', '.join(TIPOS)}")
        if origem not in ORIGENS:
            raise ValueError(f"origem inválida: {origem!r}; use uma de: {', '.join(ORIGENS)}")
        self._validar(ano, mes, tipo, self._item(descricao, valor, dia, categoria, tipo, tipo_investimento, ativo), {})
        with self._transacao():
            registro_mes = self._mes(ano, mes, criar=True)
            registro = self._inserir_lancamento(
                registro_mes, tipo, descricao, para_centavos(valor), dia, categoria, tipo_investimento, ativo, origem
            )
            self.sessao.flush()
            return registro.id

    def editar_lancamento(self, id_: int, **campos) -> None:
        desconhecidos = set(campos) - _CAMPOS_EDITAVEIS
        if desconhecidos:
            raise TypeError(f"campos não editáveis: {', '.join(sorted(desconhecidos))}")
        registro = self._achar(self._ativos(), id_)
        mes = self.sessao.get(MesRegistro, registro.mes_id)
        novo = {
            "descricao": registro.descricao,
            "valor": de_centavos(registro.valor_centavos),
            "dia": registro.dia,
            "categoria": registro.categoria,
            "tipo_investimento": registro.tipo_investimento,
            "ativo": registro.ativo,
            **campos,
        }
        item = self._item(
            novo["descricao"], novo["valor"], novo["dia"], novo["categoria"], registro.tipo,
            novo["tipo_investimento"], novo["ativo"],
        )
        self._validar(mes.ano, mes.mes, registro.tipo, item, {})
        with self._transacao():
            registro.descricao = novo["descricao"]
            registro.valor_centavos = para_centavos(novo["valor"])
            registro.dia = novo["dia"]
            registro.categoria = novo["categoria"] if novo["categoria"] is not None else "geral"
            if registro.tipo == "investimento":
                registro.tipo_investimento = novo["tipo_investimento"]
                registro.ativo = novo["ativo"]

    # ------------------------------------------------------------ lixeira (STO-12 a STO-14)

    def apagar_lancamento(self, id_: int) -> None:
        """Exclusão lógica: o lançamento vai para a lixeira e some de todas as leituras."""
        with self._transacao():
            self._achar(self._ativos(), id_).apagado_em = agora()

    def restaurar(self, id_: int) -> None:
        with self._transacao():
            self._achar(self._apagados(), id_).apagado_em = None

    def excluir_definitivamente(self, id_: int) -> None:
        with self._transacao():
            self.sessao.delete(self._achar(self._apagados(), id_))

    def esvaziar_lixeira(self) -> int:
        with self._transacao():
            resultado = self.sessao.execute(
                delete(LancamentoRegistro).where(
                    LancamentoRegistro.usuario_id == self.usuario_id, LancamentoRegistro.apagado_em.is_not(None)
                )
            )
            return resultado.rowcount

    def listar_lixeira(self) -> list[LancamentoDados]:
        return self._listar(self._apagados())

    def obter_lancamento(self, id_: int) -> LancamentoDados:
        """Um lançamento do dono, vivo ou na lixeira."""
        for consulta in (self._ativos(), self._apagados()):
            encontrados = self._listar(consulta.where(LancamentoRegistro.id == id_))
            if encontrados:
                return encontrados[0]
        raise LancamentoInexistente(id_)

    def dados_do_mes(self, ano: int, mes: int) -> tuple[Decimal | None, Decimal | None]:
        """Salário e meta cadastrados no mês (None quando não definidos)."""
        registro = self._mes(ano, mes, criar=False)
        if registro is None:
            return None, None
        salario, meta = registro.salario_centavos, registro.meta_investimento_centavos
        return (
            None if salario is None else de_centavos(salario),
            None if meta is None else de_centavos(meta),
        )

    # ------------------------------------------------------------ leitura

    def meses(self) -> list[tuple[int, int]]:
        """Meses que o usuário tem (inclusive vazios), em ordem cronológica."""
        linhas = self.sessao.execute(
            select(MesRegistro.ano, MesRegistro.mes)
            .where(MesRegistro.usuario_id == self.usuario_id)
            .order_by(MesRegistro.ano, MesRegistro.mes)
        ).all()
        return [(ano, mes) for ano, mes in linhas]

    def listar_mes(self, ano: int, mes: int) -> list[LancamentoDados]:
        return self._listar(self._ativos().where(MesRegistro.ano == ano, MesRegistro.mes == mes))

    def _meses_com_itens(
        self, ano: int | None = None, mes: int | None = None
    ) -> list[tuple[MesRegistro, list[LancamentoRegistro]]]:
        consulta = select(MesRegistro).where(MesRegistro.usuario_id == self.usuario_id)
        if ano is not None:
            consulta = consulta.where(MesRegistro.ano == ano)
        if mes is not None:
            consulta = consulta.where(MesRegistro.mes == mes)
        registros = list(self.sessao.scalars(consulta.order_by(MesRegistro.ano, MesRegistro.mes)))
        itens: dict[int, list[LancamentoRegistro]] = {}
        for item in self.sessao.scalars(self._ativos().order_by(LancamentoRegistro.id)):
            itens.setdefault(item.mes_id, []).append(item)
        return [(registro, itens.get(registro.id, [])) for registro in registros]

    def carregar_livro(self, *, ano: int | None = None, mes: int | None = None) -> LivroCaixa:
        """O `LivroCaixa` do usuário, igual ao que o loader montaria do JSON equivalente (STO-10).

        `ano` e `mes` recortam o resultado (útil para não ler tudo a cada requisição).
        """
        livro = LivroCaixa()
        for registro, itens in self._meses_com_itens(ano, mes):
            atual = livro.ano(registro.ano).mes(registro.mes)
            ancora = date(registro.ano, registro.mes, 1)
            if registro.salario_centavos:
                atual.receitas.append(Receita("Salário", de_centavos(registro.salario_centavos), ancora, "salario"))
            for item in itens:
                quando = date(registro.ano, registro.mes, item.dia)
                valor = de_centavos(item.valor_centavos)
                if item.tipo == "receita":
                    atual.receitas.append(Receita(item.descricao, valor, quando, item.categoria))
                elif item.tipo == "despesa":
                    atual.despesas.append(Despesa(item.descricao, valor, quando, item.categoria))
                else:
                    atual.investimentos.append(
                        Investimento(
                            item.descricao, valor, quando, item.categoria,
                            tipo=item.tipo_investimento or "", ativo=item.ativo or "",
                        )
                    )
            meta = registro.meta_investimento_centavos
            atual.meta_investimento = de_centavos(meta) if meta is not None else Decimal(0)
        return livro

    # ------------------------------------------------------------ JSON (STO-08, STO-09)

    def exportar_documento(self) -> dict:
        """Os dados vivos no formato do JSON de entrada (a lixeira fica de fora)."""
        anos: dict[int, list[dict]] = {}
        for registro, itens in self._meses_com_itens():
            mes: dict = {"mes": registro.mes}
            if registro.salario_centavos is not None:
                mes["salario"] = _numero_json(registro.salario_centavos)
            if registro.meta_investimento_centavos is not None:
                mes["meta_investimento"] = _numero_json(registro.meta_investimento_centavos)
            for tipo, lista in _LISTA_DO_TIPO.items():
                mes[lista] = []
                for item in (i for i in itens if i.tipo == tipo):
                    saida: dict = {
                        "descricao": item.descricao,
                        "valor": _numero_json(item.valor_centavos),
                        "dia": item.dia,
                        "categoria": item.categoria,
                    }
                    if tipo == "investimento":
                        saida["tipo"] = item.tipo_investimento
                        if item.ativo:
                            saida["ativo"] = item.ativo
                    mes[lista].append(saida)
            anos.setdefault(registro.ano, []).append(mes)
        return {"moeda": "BRL", "anos": [{"ano": ano, "meses": meses} for ano, meses in sorted(anos.items())]}

    def _mes_existe(self, ano: int, mes: int) -> bool:
        registro = self._mes(ano, mes, criar=False)
        if registro is None:
            return False
        if registro.salario_centavos is not None or registro.meta_investimento_centavos is not None:
            return True
        return self.sessao.scalars(self._ativos().where(LancamentoRegistro.mes_id == registro.id)).first() is not None

    def importar_documento(self, dados: object, *, substituir: bool = False) -> ResultadoImportacao:
        """Importa o JSON de entrada: valida, recusa meses existentes e grava tudo ou nada."""
        erros = validar(dados)
        if erros:
            raise ErroDeValidacaoJSON(erros)

        pedidos = [(int(a["ano"]), m) for a in dados["anos"] for m in a["meses"]]  # type: ignore[index]
        meses = sorted({(ano, int(m["mes"])) for ano, m in pedidos})
        existentes = [par for par in meses if self._mes_existe(*par)]
        if existentes and not substituir:
            raise MesJaExiste(existentes)

        criados = substituidos = 0
        with self._transacao():
            for ano, mes in existentes:
                substituidos += self._esvaziar_mes(ano, mes)
            for ano, m in pedidos:
                registro_mes = self._mes(ano, int(m["mes"]), criar=True)
                if "salario" in m:
                    registro_mes.salario_centavos = para_centavos(Decimal(str(m["salario"])))
                if "meta_investimento" in m:
                    registro_mes.meta_investimento_centavos = para_centavos(Decimal(str(m["meta_investimento"])))
                for tipo, lista in _LISTA_DO_TIPO.items():
                    for item in m.get(lista, []):
                        self._inserir_lancamento(
                            registro_mes, tipo, item["descricao"], para_centavos(Decimal(str(item["valor"]))),
                            item["dia"], item.get("categoria", "geral"),
                            item.get("tipo") if tipo == "investimento" else None,
                            item.get("ativo") if tipo == "investimento" else None,
                            "importado_json",
                        )
                        criados += 1
        return ResultadoImportacao(lancamentos_criados=criados, meses=meses, substituidos=substituidos)

    def _esvaziar_mes(self, ano: int, mes: int) -> int:
        """Manda os lançamentos vivos do mês para a lixeira e zera salário e meta."""
        registro = self._mes(ano, mes, criar=False)
        resultado = self.sessao.execute(
            update(LancamentoRegistro)
            .where(
                LancamentoRegistro.usuario_id == self.usuario_id,
                LancamentoRegistro.mes_id == registro.id,
                LancamentoRegistro.apagado_em.is_(None),
            )
            .values(apagado_em=agora())
        )
        registro.salario_centavos = None
        registro.meta_investimento_centavos = None
        return resultado.rowcount
