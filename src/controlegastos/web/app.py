"""Aplicação FastAPI: rotas sob /api (specs/api)."""

import io
import json
import secrets
import zipfile
from collections.abc import Iterator
from dataclasses import dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Annotated, Literal

from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException as StarletteHTTPException

from ..armazenamento import (
    LancamentoDados,
    LancamentoInexistente,
    MesJaExiste,
    Repositorio,
    aplicar_migracoes,
    criar_engine,
    criar_sessao,
)
from ..armazenamento.modelos import Usuario
from ..exportador_csv import caminhos_csv, exportar_csv_bytes
from ..generator import gerar_planilha_bytes
from ..loader import ErroDeValidacaoJSON
from ..modelo import Mes
from ..resumo import (
    livro_ate_o_ano,
    livro_do_ano,
    patrimonio_acumulado,
    percentual,
    ranking_despesas,
    totais_por_classe,
    variacao_saldo,
)
from . import esquemas as es
from .config import Configuracao
from .seguranca import (
    SESSAO_SEGUNDOS,
    LimitadorDeLogin,
    assinar_sessao,
    ler_sessao,
    verificar_contra_falso,
    verificar_hash,
)

NOME_DO_COOKIE = "sessao"
MIME_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
_MENSAGENS_HTTP = {404: "Recurso não encontrado.", 405: "Método não permitido."}


@dataclass(frozen=True, slots=True)
class Sessao:
    usuario: Usuario
    csrf: str


# ---------------------------------------------------------------- erros em português


def _erro_json(status: int, corpo: dict, cabecalhos: dict[str, str] | None = None) -> JSONResponse:
    return JSONResponse(corpo, status_code=status, headers=cabecalhos)


def _mensagem(erro: dict, campo: str) -> str:
    tipo = erro["type"]
    if tipo == "missing":
        return f"campo obrigatório '{campo}' ausente"
    if tipo in ("int_type", "int_parsing", "int_from_float"):
        return f"{campo} deve ser um inteiro"
    if tipo in ("string_type", "string_too_short"):
        return f"{campo} deve ser texto"
    if tipo == "literal_error":
        return f"{campo} inválido; use um de: receita, despesa, investimento"
    if tipo == "extra_forbidden":
        return f"campo desconhecido '{campo}'"
    if tipo == "bool_type":
        return f"{campo} deve ser verdadeiro ou falso"
    if tipo == "value_error":
        return str(erro.get("ctx", {}).get("error", f"{campo} inválido"))
    if tipo == "json_invalid":
        return "JSON inválido no corpo da requisição"
    return f"{campo} inválido"


def _erros_do_pydantic(excecao: RequestValidationError) -> list[dict]:
    resultado = []
    for erro in excecao.errors():
        local = [str(p) for p in erro["loc"]]
        if local and local[0] == "body" or local and local[0] in ("query", "path"):
            local = local[1:]
        caminho = ".".join(local) or "(raiz)"
        campo = local[-1] if local else "corpo"
        resultado.append({"caminho": caminho, "mensagem": _mensagem(erro, campo)})
    return resultado


def _registrar_tratadores(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def _validacao(_req: Request, excecao: RequestValidationError):
        return _erro_json(422, {"erros": _erros_do_pydantic(excecao)})

    @app.exception_handler(ErroDeValidacaoJSON)
    async def _validacao_json(_req: Request, excecao: ErroDeValidacaoJSON):
        return _erro_json(422, {"erros": [{"caminho": e.caminho, "mensagem": e.mensagem} for e in excecao.erros]})

    @app.exception_handler(LancamentoInexistente)
    async def _inexistente(_req: Request, _excecao: LancamentoInexistente):
        return _erro_json(404, {"detalhe": "Lançamento não encontrado."})

    @app.exception_handler(MesJaExiste)
    async def _mes_existe(_req: Request, excecao: MesJaExiste):
        meses = [{"ano": ano, "mes": mes} for ano, mes in excecao.meses]
        return _erro_json(409, {"mensagem": str(excecao), "meses": meses})

    @app.exception_handler(StarletteHTTPException)
    async def _http(_req: Request, excecao: StarletteHTTPException):
        detalhe = _MENSAGENS_HTTP.get(excecao.status_code, excecao.detail)
        return _erro_json(excecao.status_code, {"detalhe": detalhe}, getattr(excecao, "headers", None))


# ---------------------------------------------------------------- apresentação


def _lancamento(dados: LancamentoDados) -> es.Lancamento:
    return es.Lancamento(
        id=dados.id,
        ano=dados.ano,
        mes=dados.mes,
        tipo=dados.tipo,
        descricao=dados.descricao,
        valor=es.texto_dinheiro(dados.valor),
        dia=dados.dia,
        categoria=dados.categoria,
        tipo_investimento=dados.tipo_investimento,
        ativo=dados.ativo,
        origem=dados.origem,
        apagado_em=dados.apagado_em.isoformat() if dados.apagado_em else None,
    )


def _totais(mes: Mes) -> es.Totais:
    return es.Totais(
        receitas=es.texto_dinheiro(mes.total_receitas),
        despesas=es.texto_dinheiro(mes.total_despesas),
        investimentos=es.texto_dinheiro(mes.total_investimentos),
        saldo_livre=es.texto_dinheiro(mes.saldo_livre),
    )


def _classes(mes: Mes) -> list[es.Classe]:
    total = mes.total_investimentos
    if not total:
        return []
    return [
        es.Classe(tipo=tipo, total=es.texto_dinheiro(subtotal), percentual=es.texto_dinheiro(percentual(subtotal, total)))
        for tipo, subtotal in sorted(totais_por_classe(mes).items())
    ]


def _meta(mes: Mes) -> es.Meta | None:
    if not mes.meta_investimento:
        return None
    diferenca = mes.meta_investimento - mes.total_investimentos
    return es.Meta(
        valor=es.texto_dinheiro(mes.meta_investimento),
        investido=es.texto_dinheiro(mes.total_investimentos),
        diferenca=es.texto_dinheiro(diferenca),
        situacao="falta" if diferenca > 0 else "acima",
    )


def _opcional(valor: Decimal | None) -> str | None:
    return None if valor is None else es.texto_dinheiro(valor)


# ---------------------------------------------------------------- aplicação


def criar_app(config: Configuracao | None = None) -> FastAPI:
    config = config or Configuracao.do_ambiente()
    if not config.chave_secreta:
        if config.cookie_secure:
            raise RuntimeError(
                "No modo hospedado (CONTROLEGASTOS_COOKIE_SECURE=1) defina CONTROLEGASTOS_CHAVE_SECRETA."
            )
        config = replace(config, chave_secreta=secrets.token_urlsafe(48))  # só local: vale por processo

    motor = criar_engine(config.database_url)
    aplicar_migracoes(motor)

    app = FastAPI(title="controleGastos", version="0.1.0", description="API do controle de gastos pessoais.")
    app.state.config = config
    app.state.motor = motor
    app.state.limitador = LimitadorDeLogin()
    _registrar_tratadores(app)

    def banco() -> Iterator[Session]:
        with criar_sessao(motor) as sessao:
            yield sessao

    def sessao_atual(request: Request, db: Annotated[Session, Depends(banco)]) -> Sessao:
        nao_autenticado = HTTPException(401, "É preciso entrar para continuar.")
        token = request.cookies.get(NOME_DO_COOKIE)
        dados = ler_sessao(token, config.chave_secreta) if token else None
        if not dados or "uid" not in dados or "csrf" not in dados:
            raise nao_autenticado
        usuario = db.scalar(select(Usuario).where(Usuario.id == dados["uid"]))
        if usuario is None:
            raise nao_autenticado
        return Sessao(usuario=usuario, csrf=dados["csrf"])

    def com_csrf(request: Request, sessao: Annotated[Sessao, Depends(sessao_atual)]) -> Sessao:
        enviado = request.headers.get("x-csrf-token", "")
        if not secrets.compare_digest(enviado.encode(), sessao.csrf.encode()):
            raise HTTPException(403, "Token CSRF ausente ou inválido.")
        return sessao

    def repositorio(db: Annotated[Session, Depends(banco)], sessao: Annotated[Sessao, Depends(sessao_atual)]) -> Repositorio:
        return Repositorio(db, sessao.usuario.id)

    def repositorio_escrita(db: Annotated[Session, Depends(banco)], sessao: Annotated[Sessao, Depends(com_csrf)]) -> Repositorio:
        return Repositorio(db, sessao.usuario.id)

    Leitura = Annotated[Repositorio, Depends(repositorio)]
    Escrita = Annotated[Repositorio, Depends(repositorio_escrita)]
    Erros = {422: {"model": es.ErrosValidacao}, 401: {"model": es.Detalhe}}

    # -------------------------------------------------------------- conta

    @app.post("/api/auth/login", response_model=es.Usuario, responses={401: {"model": es.Detalhe}, 429: {"model": es.Detalhe}}, tags=["conta"])
    def login(corpo: es.LoginEntrada, request: Request, resposta: Response, db: Annotated[Session, Depends(banco)]):
        chave = (corpo.nome.strip().lower(), request.client.host if request.client else "?")
        espera = app.state.limitador.segundos_de_bloqueio(chave)
        if espera:
            raise HTTPException(
                429,
                "Muitas tentativas de login. Aguarde alguns minutos e tente de novo.",
                headers={"Retry-After": str(espera)},
            )
        usuario = db.scalar(select(Usuario).where(Usuario.nome == corpo.nome.strip()))
        if usuario is None:
            verificar_contra_falso(corpo.senha)
        if usuario is None or not verificar_hash(corpo.senha, usuario.senha_hash):
            app.state.limitador.registrar_falha(chave)
            raise HTTPException(401, "Usuário ou senha inválidos.")
        app.state.limitador.registrar_sucesso(chave)
        csrf = secrets.token_urlsafe(32)
        resposta.set_cookie(
            NOME_DO_COOKIE,
            assinar_sessao({"uid": usuario.id, "csrf": csrf}, config.chave_secreta),
            max_age=SESSAO_SEGUNDOS,
            httponly=True,
            samesite="lax",
            secure=config.cookie_secure,
            path="/",
        )
        return es.Usuario(id=usuario.id, nome=usuario.nome, csrf_token=csrf)

    @app.post("/api/auth/logout", status_code=204, tags=["conta"])
    def logout(resposta: Response):
        resposta.delete_cookie(NOME_DO_COOKIE, path="/")
        resposta.status_code = 204
        return resposta

    @app.get("/api/me", response_model=es.Usuario, responses={401: {"model": es.Detalhe}}, tags=["conta"])
    def eu(sessao: Annotated[Sessao, Depends(sessao_atual)]):
        return es.Usuario(id=sessao.usuario.id, nome=sessao.usuario.nome, csrf_token=sessao.csrf)

    # -------------------------------------------------------------- meses e lançamentos

    @app.get("/api/meses/{ano}/{mes}", response_model=es.MesSaida, responses=Erros, tags=["meses"])
    def ver_mes(ano: int, mes: int, repo: Leitura):
        livro = repo.carregar_livro(ano=ano, mes=mes)
        atual = livro.anos[ano].meses[mes] if ano in livro.anos and mes in livro.anos[ano].meses else Mes(numero=mes, ano=ano)
        salario, meta = repo.dados_do_mes(ano, mes)
        itens = sorted(repo.listar_mes(ano, mes), key=lambda i: (i.dia, i.id))
        return es.MesSaida(
            ano=ano,
            mes=mes,
            salario=_opcional(salario),
            meta_investimento=_opcional(meta),
            lancamentos=[_lancamento(i) for i in itens],
            totais=_totais(atual),
            investimentos_por_classe=_classes(atual),
            meta=_meta(atual),
        )

    @app.put("/api/meses/{ano}/{mes}", response_model=es.MesSaida, responses=Erros, tags=["meses"])
    def definir_mes(ano: int, mes: int, corpo: es.MesEntrada, repo: Escrita):
        enviados = {campo: getattr(corpo, campo) for campo in corpo.model_fields_set}
        repo.definir_mes(ano, mes, **enviados)
        return ver_mes(ano, mes, repo)

    @app.post("/api/lancamentos", status_code=201, response_model=es.Lancamento, responses=Erros, tags=["lançamentos"])
    def criar_lancamento(corpo: es.LancamentoEntrada, repo: Escrita):
        id_ = repo.adicionar_lancamento(
            corpo.ano, corpo.mes, corpo.tipo, corpo.descricao, corpo.valor, corpo.dia,
            categoria=corpo.categoria if corpo.categoria is not None else "geral",
            tipo_investimento=corpo.tipo_investimento, ativo=corpo.ativo,
        )
        return _lancamento(repo.obter_lancamento(id_))

    @app.patch("/api/lancamentos/{id}", response_model=es.Lancamento, responses={**Erros, 404: {"model": es.Detalhe}}, tags=["lançamentos"])
    def editar_lancamento(id: int, corpo: es.LancamentoAtualizacao, repo: Escrita):
        repo.editar_lancamento(id, **{campo: getattr(corpo, campo) for campo in corpo.model_fields_set})
        return _lancamento(repo.obter_lancamento(id))

    @app.delete("/api/lancamentos/{id}", status_code=204, responses={404: {"model": es.Detalhe}}, tags=["lançamentos"])
    def apagar_lancamento(id: int, repo: Escrita):
        repo.apagar_lancamento(id)
        return Response(status_code=204)

    # -------------------------------------------------------------- painel do ano

    @app.get("/api/anos/{ano}/resumo", response_model=es.AnoSaida, responses=Erros, tags=["painéis"])
    def resumo_do_ano(ano: int, repo: Leitura):
        completo = repo.carregar_livro()
        do_ano = livro_do_ano(completo, ano)
        meses = do_ano.anos[ano].meses if ano in do_ano.anos else {}
        rotulo_do_ano = f"{ano}-"
        return es.AnoSaida(
            ano=ano,
            meses=[
                es.ResumoMes(
                    mes=numero,
                    receitas=es.texto_dinheiro(m.total_receitas),
                    despesas=es.texto_dinheiro(m.total_despesas),
                    investimentos=es.texto_dinheiro(m.total_investimentos),
                    saldo_livre=es.texto_dinheiro(m.saldo_livre),
                )
                for numero, m in sorted(meses.items())
            ],
            patrimonio=[
                es.PontoSerie(rotulo=r, valor=es.texto_dinheiro(v))
                for r, v in patrimonio_acumulado(livro_ate_o_ano(completo, ano))
                if r.startswith(rotulo_do_ano)
            ],
            ranking=[es.ItemRanking(categoria=c, total=es.texto_dinheiro(v)) for c, v in ranking_despesas(do_ano)],
            variacao=[es.PontoSerie(rotulo=r, valor=es.texto_dinheiro(v)) for r, v in variacao_saldo(do_ano)],
        )

    # -------------------------------------------------------------- arquivos

    @app.get("/api/exportar/{formato}", responses={401: {"model": es.Detalhe}, 200: {"description": "Arquivo gerado."}}, tags=["arquivos"])
    def exportar(formato: Literal["xlsx", "csv", "json"], repo: Leitura, ano: Annotated[int | None, Query()] = None):
        nome = f"controlegastos-{ano if ano is not None else 'todos'}"
        cabecalho = lambda extensao: {"Content-Disposition": f'attachment; filename="{nome}.{extensao}"'}
        if formato == "json":
            documento = repo.exportar_documento()
            if ano is not None:
                documento["anos"] = [a for a in documento["anos"] if a["ano"] == ano]
            return JSONResponse(documento, headers=cabecalho("json"))
        livro = repo.carregar_livro(ano=ano)
        if formato == "xlsx":
            return Response(gerar_planilha_bytes(livro), media_type=MIME_XLSX, headers=cabecalho("xlsx"))
        lancamentos, resumo = exportar_csv_bytes(livro)
        nome_lancamentos, nome_resumo = (p.name for p in caminhos_csv(Path(nome)))
        pacote = io.BytesIO()
        with zipfile.ZipFile(pacote, "w", zipfile.ZIP_DEFLATED) as zip_:
            zip_.writestr(nome_lancamentos, lancamentos)
            zip_.writestr(nome_resumo, resumo)
        return Response(pacote.getvalue(), media_type="application/zip", headers=cabecalho("zip"))

    @app.post(
        "/api/importar/json",
        response_model=es.ResultadoImportacao,
        responses={**Erros, 409: {"model": es.Conflito}},
        openapi_extra={"requestBody": {"required": True, "content": {"application/json": {"schema": {"type": "object"}}}}},
        tags=["arquivos"],
    )
    async def importar(request: Request, repo: Escrita, substituir: bool = False):
        try:
            documento = json.loads(await request.body())
        except ValueError as erro:
            mensagem = f"JSON inválido: {erro}"
            return _erro_json(422, {"erros": [{"caminho": "(raiz)", "mensagem": mensagem}]})
        resultado = repo.importar_documento(documento, substituir=substituir)
        return es.ResultadoImportacao(
            lancamentos_criados=resultado.lancamentos_criados,
            meses=[es.MesRef(ano=a, mes=m) for a, m in resultado.meses],
            substituidos=resultado.substituidos,
        )

    # -------------------------------------------------------------- lixeira

    @app.get("/api/lixeira", response_model=list[es.Lancamento], responses={401: {"model": es.Detalhe}}, tags=["lixeira"])
    def listar_lixeira(repo: Leitura):
        return [_lancamento(i) for i in repo.listar_lixeira()]

    @app.post("/api/lixeira/{id}/restaurar", response_model=es.Lancamento, responses={404: {"model": es.Detalhe}}, tags=["lixeira"])
    def restaurar(id: int, repo: Escrita):
        repo.restaurar(id)
        return _lancamento(repo.obter_lancamento(id))

    @app.delete("/api/lixeira/{id}", status_code=204, responses={404: {"model": es.Detalhe}}, tags=["lixeira"])
    def excluir_definitivamente(id: int, repo: Escrita):
        repo.excluir_definitivamente(id)
        return Response(status_code=204)

    @app.delete("/api/lixeira", response_model=es.Removidos, responses={401: {"model": es.Detalhe}}, tags=["lixeira"])
    def esvaziar(repo: Escrita):
        return es.Removidos(removidos=repo.esvaziar_lixeira())

    return app
