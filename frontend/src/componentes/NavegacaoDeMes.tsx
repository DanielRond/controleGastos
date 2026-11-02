import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { nomeDoMes } from "../formato";

function vizinho(ano: number, mes: number, delta: number): { ano: number; mes: number } {
  const indice = ano * 12 + (mes - 1) + delta;
  return { ano: Math.floor(indice / 12), mes: (indice % 12) + 1 };
}

export function NavegacaoDeMes({ ano, mes }: { ano: number; mes: number }) {
  const navegar = useNavigate();
  const anterior = vizinho(ano, mes, -1);
  const seguinte = vizinho(ano, mes, 1);
  const [anoEscolhido, setAnoEscolhido] = useState(String(ano));
  const [mesEscolhido, setMesEscolhido] = useState(String(mes));

  function ir(evento: FormEvent) {
    evento.preventDefault();
    const a = Number(anoEscolhido);
    if (Number.isInteger(a) && a >= 1 && a <= 9999) navegar(`/mes/${a}/${mesEscolhido}`);
  }

  return (
    <nav className="navegacao-mes" aria-label="Escolher mês">
      <Link to={`/mes/${anterior.ano}/${anterior.mes}`} rel="prev">
        ← {nomeDoMes(anterior.mes)} de {anterior.ano}
      </Link>
      <form onSubmit={ir} className="escolha">
        <label htmlFor="escolha-mes">Mês</label>
        <select id="escolha-mes" value={mesEscolhido} onChange={(e) => setMesEscolhido(e.target.value)}>
          {Array.from({ length: 12 }, (_, i) => (
            <option key={i + 1} value={i + 1}>
              {nomeDoMes(i + 1)}
            </option>
          ))}
        </select>
        <label htmlFor="escolha-ano">Ano</label>
        <input id="escolha-ano" type="number" min={1} max={9999} value={anoEscolhido} onChange={(e) => setAnoEscolhido(e.target.value)} />
        <button type="submit" className="secundario">
          Ir
        </button>
      </form>
      <Link to={`/mes/${seguinte.ano}/${seguinte.mes}`} rel="next">
        {nomeDoMes(seguinte.mes)} de {seguinte.ano} →
      </Link>
    </nav>
  );
}
