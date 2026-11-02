import type { Lancamento } from "../api/tipos";
import { rotuloDaClasse } from "../api/tipos";
import { formatarReais } from "../formato";

const ROTULO_DO_TIPO: Record<string, string> = { receita: "Receita", despesa: "Despesa", investimento: "Investimento" };

interface Props {
  lancamentos: Lancamento[];
  aoEditar: (lancamento: Lancamento) => void;
  aoApagar: (lancamento: Lancamento) => void;
}

export function TabelaLancamentos({ lancamentos, aoEditar, aoApagar }: Props) {
  if (lancamentos.length === 0) return <p className="aviso">Nenhum lançamento neste mês.</p>;
  return (
    <table aria-label="Lançamentos do mês">
      <thead>
        <tr>
          <th>Dia</th>
          <th>Descrição</th>
          <th>Tipo</th>
          <th>Categoria</th>
          <th className="valor">Valor</th>
          <th>Ações</th>
        </tr>
      </thead>
      <tbody>
        {lancamentos.map((item) => (
          <tr key={item.id}>
            <td>{item.dia}</td>
            <td>{item.descricao}</td>
            <td>
              {ROTULO_DO_TIPO[item.tipo] ?? item.tipo}
              {item.tipo === "investimento" && item.tipo_investimento && (
                <small>
                  {" "}
                  ({rotuloDaClasse(item.tipo_investimento)}
                  {item.ativo ? `, ${item.ativo}` : ""})
                </small>
              )}
            </td>
            <td>{item.categoria}</td>
            <td className="valor">{formatarReais(item.valor)}</td>
            <td className="acoes">
              <button type="button" className="secundario" onClick={() => aoEditar(item)} aria-label={`Editar ${item.descricao}`}>
                Editar
              </button>
              <button type="button" className="perigo" onClick={() => aoApagar(item)} aria-label={`Apagar ${item.descricao}`}>
                Apagar
              </button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
