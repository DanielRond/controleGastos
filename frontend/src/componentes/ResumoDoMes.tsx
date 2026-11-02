import type { MesSaida } from "../api/tipos";
import { rotuloDaClasse } from "../api/tipos";
import { formatarReais } from "../formato";

export function ResumoDoMes({ mes }: { mes: MesSaida }) {
  const { totais, meta } = mes;
  return (
    <section aria-labelledby="titulo-resumo">
      <h2 id="titulo-resumo">Resumo do mês</h2>
      <dl className="totais">
        <div>
          <dt>Receitas</dt>
          <dd>{formatarReais(totais.receitas)}</dd>
        </div>
        <div>
          <dt>Despesas</dt>
          <dd>{formatarReais(totais.despesas)}</dd>
        </div>
        <div>
          <dt>Investimentos</dt>
          <dd>{formatarReais(totais.investimentos)}</dd>
        </div>
        <div>
          <dt>Saldo livre</dt>
          <dd>{formatarReais(totais.saldo_livre)}</dd>
        </div>
      </dl>

      {mes.investimentos_por_classe.length > 0 && (
        <table aria-label="Investimentos por classe">
          <thead>
            <tr>
              <th>Classe</th>
              <th className="valor">Total</th>
              <th className="valor">% do investido</th>
            </tr>
          </thead>
          <tbody>
            {mes.investimentos_por_classe.map((classe) => (
              <tr key={classe.tipo}>
                <td>{rotuloDaClasse(classe.tipo)}</td>
                <td className="valor">{formatarReais(classe.total)}</td>
                <td className="valor">{classe.percentual.replace(".", ",")}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {meta && (
        <p className="meta" role="status">
          Meta de investimento: {formatarReais(meta.valor)}.{" "}
          {meta.situacao === "falta"
            ? `Faltam ${formatarReais(meta.diferenca)}.`
            : meta.diferenca.replace("-", "") === "0.00"
              ? "Meta atingida."
              : `Meta ultrapassada em ${formatarReais(meta.diferenca.replace("-", ""))}.`}
        </p>
      )}
    </section>
  );
}
