import { useEffect, useRef, useState, type FormEvent } from "react";
import { api, errosDeValidacao, mensagemDe } from "../api/cliente";
import type { Lancamento, TipoDeLancamento } from "../api/tipos";
import { TIPOS_DE_INVESTIMENTO } from "../api/tipos";
import { lerDinheiro, paraCampo } from "../formato";

const CAMPOS = ["tipo", "dia", "descricao", "valor", "categoria", "tipo_investimento", "ativo"] as const;
type Campo = (typeof CAMPOS)[number];
type Erros = Partial<Record<Campo, string>> & { geral?: string[] };

interface Props {
  ano: number;
  mes: number;
  inicial?: Lancamento;
  aoSalvar: () => void;
  aoCancelar?: () => void;
}

export function FormularioLancamento({ ano, mes, inicial, aoSalvar, aoCancelar }: Props) {
  const editando = inicial !== undefined;
  const [tipo, setTipo] = useState<TipoDeLancamento>((inicial?.tipo as TipoDeLancamento) ?? "despesa");
  const [dia, setDia] = useState(String(inicial?.dia ?? ""));
  const [descricao, setDescricao] = useState(inicial?.descricao ?? "");
  const [valor, setValor] = useState(inicial ? paraCampo(inicial.valor) : "");
  const [categoria, setCategoria] = useState(inicial?.categoria ?? "");
  const [tipoInvestimento, setTipoInvestimento] = useState(inicial?.tipo_investimento ?? "renda_fixa");
  const [ativo, setAtivo] = useState(inicial?.ativo ?? "");
  const [erros, setErros] = useState<Erros>({});
  const [enviando, setEnviando] = useState(false);
  const focarDepois = useRef(false);
  const campoDia = useRef<HTMLInputElement>(null);

  // Depois de enviar, o foco volta ao primeiro campo para o próximo lançamento (só quando o formulário volta a ficar ativo).
  useEffect(() => {
    if (!enviando && focarDepois.current) {
      focarDepois.current = false;
      campoDia.current?.focus();
    }
  }, [enviando]);

  async function enviar(evento: FormEvent) {
    evento.preventDefault();
    setErros({});
    const leitura = lerDinheiro(valor);
    if (!leitura.ok) {
      setErros({ valor: leitura.erro });
      return;
    }
    const corpo = {
      descricao,
      valor: leitura.valor,
      dia: Number(dia),
      categoria: categoria.trim() === "" ? undefined : categoria.trim(),
      ...(tipo === "investimento" ? { tipo_investimento: tipoInvestimento, ativo: ativo.trim() || undefined } : {}),
    };
    setEnviando(true);
    try {
      const resposta = editando
        ? await api.PATCH("/api/lancamentos/{id}", { params: { path: { id: inicial.id } }, body: corpo })
        : await api.POST("/api/lancamentos", { body: { ano, mes, tipo, ...corpo } });
      if (!resposta.error) {
        aoSalvar();
        if (!editando) {
          setDescricao("");
          setValor("");
          setDia("");
          setCategoria("");
          setAtivo("");
          focarDepois.current = true;
        }
        return;
      }
      const lista = errosDeValidacao(resposta.error);
      if (lista) {
        const novos: Erros = { geral: [] };
        for (const { caminho, mensagem } of lista) {
          if ((CAMPOS as readonly string[]).includes(caminho)) novos[caminho as Campo] = mensagem;
          else novos.geral!.push(`${caminho}: ${mensagem}`);
        }
        setErros(novos);
      } else {
        setErros({ geral: [mensagemDe(resposta.error, "Não foi possível salvar o lançamento.")] });
      }
    } catch {
      setErros({ geral: ["Não foi possível falar com o servidor. Tente novamente."] });
    } finally {
      setEnviando(false);
    }
  }

  function campoComErro(campo: Campo, rotulo: string, entrada: (descricaoDoErro: string | undefined) => React.ReactNode) {
    const erro = erros[campo];
    return (
      <div className="campo">
        <label htmlFor={`lanc-${campo}`}>{rotulo}</label>
        {entrada(erro ? `erro-${campo}` : undefined)}
        {erro && (
          <span id={`erro-${campo}`} role="alert" className="erro">
            {erro}
          </span>
        )}
      </div>
    );
  }

  return (
    <form onSubmit={enviar} className="cartao formulario" aria-labelledby="titulo-formulario" noValidate>
      <h2 id="titulo-formulario">{editando ? "Editar lançamento" : "Novo lançamento"}</h2>
      {/* Desabilitado durante o envio: nada digitado nesse intervalo se perde quando a resposta chega. */}
      <fieldset disabled={enviando} className="sem-borda">

      {campoComErro("tipo", "Tipo", (d) => (
        <select id="lanc-tipo" value={tipo} disabled={editando} aria-invalid={!!erros.tipo} aria-describedby={d} onChange={(e) => setTipo(e.target.value as TipoDeLancamento)}>
          <option value="despesa">Despesa</option>
          <option value="receita">Receita</option>
          <option value="investimento">Investimento</option>
        </select>
      ))}
      {campoComErro("dia", "Dia", (d) => (
        <input ref={campoDia} id="lanc-dia" type="number" min={1} max={31} value={dia} aria-invalid={!!erros.dia} aria-describedby={d} onChange={(e) => setDia(e.target.value)} />
      ))}
      {campoComErro("descricao", "Descrição", (d) => (
        <input id="lanc-descricao" value={descricao} aria-invalid={!!erros.descricao} aria-describedby={d} onChange={(e) => setDescricao(e.target.value)} />
      ))}
      {campoComErro("valor", "Valor (R$)", (d) => (
        <input id="lanc-valor" inputMode="decimal" placeholder="0,00" value={valor} aria-invalid={!!erros.valor} aria-describedby={d} onChange={(e) => setValor(e.target.value)} />
      ))}
      {campoComErro("categoria", "Categoria", (d) => (
        <input id="lanc-categoria" value={categoria} placeholder="geral" aria-invalid={!!erros.categoria} aria-describedby={d} onChange={(e) => setCategoria(e.target.value)} />
      ))}
      {tipo === "investimento" && (
        <>
          {campoComErro("tipo_investimento", "Classe do investimento", (d) => (
            <select id="lanc-tipo_investimento" value={tipoInvestimento} aria-invalid={!!erros.tipo_investimento} aria-describedby={d} onChange={(e) => setTipoInvestimento(e.target.value)}>
              {TIPOS_DE_INVESTIMENTO.map((t) => (
                <option key={t.valor} value={t.valor}>
                  {t.rotulo}
                </option>
              ))}
            </select>
          ))}
          {campoComErro("ativo", "Ativo (ex.: KNSC11, BTC, CDI)", (d) => (
            <input id="lanc-ativo" value={ativo} aria-invalid={!!erros.ativo} aria-describedby={d} onChange={(e) => setAtivo(e.target.value)} />
          ))}
        </>
      )}

      {erros.geral && erros.geral.length > 0 && (
        <ul role="alert" className="erro">
          {erros.geral.map((mensagem) => (
            <li key={mensagem}>{mensagem}</li>
          ))}
        </ul>
      )}
      <div className="botoes">
        <button type="submit" disabled={enviando}>
          {editando ? "Salvar alterações" : "Adicionar"}
        </button>
        {aoCancelar && (
          <button type="button" className="secundario" onClick={aoCancelar}>
            Cancelar
          </button>
        )}
      </div>
      </fieldset>
    </form>
  );
}
