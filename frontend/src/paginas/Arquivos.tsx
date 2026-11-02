import { useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api, errosDeValidacao, mensagemDe, type ErroCampo } from "../api/cliente";
import { Confirmacao } from "../componentes/Confirmacao";
import { mesAtual } from "../formato";

type Resultado =
  | { tipo: "sucesso"; texto: string }
  | { tipo: "erros"; erros: ErroCampo[] }
  | { tipo: "conflito"; mensagem: string }
  | { tipo: "falha"; texto: string };

const rotuloDoMes = (m: { ano: number; mes: number }) => `${m.ano}-${String(m.mes).padStart(2, "0")}`;

export function Arquivos() {
  const clienteDeConsultas = useQueryClient();
  const [filtro, setFiltro] = useState<"todos" | "ano">("todos");
  const [ano, setAno] = useState(String(mesAtual().ano));
  const [documento, setDocumento] = useState<unknown>(null);
  const [resultado, setResultado] = useState<Resultado | null>(null);
  const [confirmando, setConfirmando] = useState(false);
  const [enviando, setEnviando] = useState(false);

  const consulta = filtro === "ano" && /^\d{1,4}$/.test(ano) ? `?ano=${Number(ano)}` : "";

  async function importar(corpo: unknown, substituir: boolean) {
    setEnviando(true);
    setConfirmando(false);
    try {
      const { data, error, response } = await api.POST("/api/importar/json", {
        params: { query: { substituir } },
        body: corpo as never,
      });
      if (data) {
        const meses = data.meses.map(rotuloDoMes).join(", ");
        const trocados = data.substituidos > 0 ? ` ${data.substituidos} lançamentos antigos foram para a lixeira.` : "";
        setResultado({ tipo: "sucesso", texto: `Importação concluída: ${data.lancamentos_criados} lançamentos criados (${meses}).${trocados}` });
        setDocumento(null);
        void clienteDeConsultas.invalidateQueries();
      } else if (response.status === 409) {
        setResultado({ tipo: "conflito", mensagem: (error as { mensagem?: string }).mensagem ?? "Já existem dados nesses meses." });
      } else {
        const erros = errosDeValidacao(error);
        setResultado(erros ? { tipo: "erros", erros } : { tipo: "falha", texto: mensagemDe(error, "Não foi possível importar.") });
      }
    } catch {
      setResultado({ tipo: "falha", texto: "Não foi possível falar com o servidor. Tente novamente." });
    } finally {
      setEnviando(false);
    }
  }

  async function aoEscolherArquivo(arquivo: File | undefined) {
    setResultado(null);
    setConfirmando(false);
    if (!arquivo) return;
    let lido: unknown;
    try {
      lido = JSON.parse(await arquivo.text());
    } catch {
      setDocumento(null);
      setResultado({ tipo: "falha", texto: "O arquivo não é um JSON válido." });
      return;
    }
    setDocumento(lido);
    await importar(lido, false);
  }

  return (
    <section>
      <h1>Arquivos</h1>

      <section className="cartao" aria-labelledby="titulo-baixar">
        <h2 id="titulo-baixar">Baixar</h2>
        <fieldset>
          <legend>Período</legend>
          <label>
            <input type="radio" name="periodo" checked={filtro === "todos"} onChange={() => setFiltro("todos")} /> Todos os anos
          </label>{" "}
          <label>
            <input type="radio" name="periodo" checked={filtro === "ano"} onChange={() => setFiltro("ano")} /> Um ano
          </label>
          {filtro === "ano" && (
            <div className="campo">
              <label htmlFor="ano-arquivo">Ano</label>
              <input id="ano-arquivo" type="number" min={1} max={9999} value={ano} onChange={(e) => setAno(e.target.value)} />
            </div>
          )}
        </fieldset>
        <p className="botoes">
          <a className="botao" href={`/api/exportar/xlsx${consulta}`} download>
            Baixar planilha (.xlsx)
          </a>
          <a className="botao" href={`/api/exportar/csv${consulta}`} download>
            Baixar CSV (.zip)
          </a>
          <a className="botao" href={`/api/exportar/json${consulta}`} download>
            Exportar JSON
          </a>
        </p>
      </section>

      <section className="cartao" aria-labelledby="titulo-importar">
        <h2 id="titulo-importar">Importar JSON</h2>
        <p className="aviso">Use o mesmo formato dos arquivos de entrada. Meses que já existem não são sobrescritos sem a sua confirmação.</p>
        <div className="campo">
          <label htmlFor="arquivo-json">Arquivo JSON</label>
          <input id="arquivo-json" type="file" accept="application/json,.json" disabled={enviando} onChange={(e) => void aoEscolherArquivo(e.target.files?.[0])} />
        </div>

        {enviando && <p role="status">Importando…</p>}
        {resultado?.tipo === "sucesso" && <p role="status" className="aviso-acao">{resultado.texto}</p>}
        {resultado?.tipo === "falha" && (
          <p role="alert" className="erro">
            {resultado.texto}
          </p>
        )}
        {resultado?.tipo === "erros" && (
          <div role="alert" className="erro">
            <p>O arquivo tem {resultado.erros.length} erro(s) e nada foi importado:</p>
            <ul>
              {resultado.erros.map((e) => (
                <li key={`${e.caminho}-${e.mensagem}`}>
                  <code>{e.caminho}</code>: {e.mensagem}
                </li>
              ))}
            </ul>
          </div>
        )}
        {resultado?.tipo === "conflito" && (
          <div role="alert" className="erro">
            <p>{resultado.mensagem}</p>
            {!confirmando && (
              <button type="button" className="secundario" onClick={() => setConfirmando(true)}>
                Substituir os meses do arquivo
              </button>
            )}
          </div>
        )}
        {confirmando && (
          <Confirmacao
            mensagem="Os lançamentos atuais desses meses vão para a lixeira e os do arquivo entram no lugar. Continuar?"
            rotuloConfirmar="Substituir agora"
            aoConfirmar={() => void importar(documento, true)}
            aoCancelar={() => setConfirmando(false)}
          />
        )}
      </section>
    </section>
  );
}
