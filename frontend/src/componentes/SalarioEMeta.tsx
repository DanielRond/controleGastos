import { useState, type FormEvent } from "react";
import { api, errosDeValidacao, mensagemDe } from "../api/cliente";
import { lerDinheiro, paraCampo } from "../formato";

interface Props {
  ano: number;
  mes: number;
  salario: string | null;
  meta: string | null;
  aoSalvar: () => void;
}

/** Campo vazio limpa o valor (null); senão envia o texto decimal. */
function paraApi(campo: string): { ok: true; valor: string | null } | { ok: false; erro: string } {
  if (campo.trim() === "") return { ok: true, valor: null };
  const leitura = lerDinheiro(campo);
  return leitura.ok ? { ok: true, valor: leitura.valor } : { ok: false, erro: leitura.erro };
}

export function SalarioEMeta({ ano, mes, salario, meta, aoSalvar }: Props) {
  const [campoSalario, setCampoSalario] = useState(salario ? paraCampo(salario) : "");
  const [campoMeta, setCampoMeta] = useState(meta ? paraCampo(meta) : "");
  const [erros, setErros] = useState<Record<string, string>>({});
  const [aviso, setAviso] = useState<string | null>(null);

  async function enviar(evento: FormEvent) {
    evento.preventDefault();
    setErros({});
    setAviso(null);
    const s = paraApi(campoSalario);
    const m = paraApi(campoMeta);
    if (!s.ok || !m.ok) {
      setErros({ ...(s.ok ? {} : { salario: s.erro }), ...(m.ok ? {} : { meta_investimento: m.erro }) });
      return;
    }
    try {
      const { error } = await api.PUT("/api/meses/{ano}/{mes}", {
        params: { path: { ano, mes } },
        body: { salario: s.valor, meta_investimento: m.valor },
      });
      if (!error) {
        setAviso("Salário e meta salvos.");
        aoSalvar();
        return;
      }
      const lista = errosDeValidacao(error);
      setErros(lista ? Object.fromEntries(lista.map((e) => [e.caminho, e.mensagem])) : { geral: mensagemDe(error, "Não foi possível salvar.") });
    } catch {
      setErros({ geral: "Não foi possível falar com o servidor. Tente novamente." });
    }
  }

  const campo = (id: string, rotulo: string, valor: string, definir: (v: string) => void, chave: string) => (
    <div className="campo">
      <label htmlFor={id}>{rotulo}</label>
      <input id={id} inputMode="decimal" placeholder="0,00" value={valor} aria-invalid={!!erros[chave]} aria-describedby={erros[chave] ? `erro-${id}` : undefined} onChange={(e) => definir(e.target.value)} />
      {erros[chave] && (
        <span id={`erro-${id}`} role="alert" className="erro">
          {erros[chave]}
        </span>
      )}
    </div>
  );

  return (
    <form onSubmit={enviar} className="cartao" aria-labelledby="titulo-salario" noValidate>
      <h2 id="titulo-salario">Salário e meta do mês</h2>
      {campo("salario", "Salário (R$)", campoSalario, setCampoSalario, "salario")}
      {campo("meta", "Meta de investimento (R$)", campoMeta, setCampoMeta, "meta_investimento")}
      <p className="aviso">Deixe em branco para limpar o valor.</p>
      {erros.geral && (
        <p role="alert" className="erro">
          {erros.geral}
        </p>
      )}
      {aviso && <p role="status">{aviso}</p>}
      <button type="submit">Salvar</button>
    </form>
  );
}
