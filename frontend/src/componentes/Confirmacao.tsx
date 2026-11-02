import { useId } from "react";

interface Props {
  mensagem: string;
  rotuloConfirmar: string;
  aoConfirmar: () => void;
  aoCancelar: () => void;
}

/** Confirmação em linha; o foco começa em Cancelar (a opção segura). */
export function Confirmacao({ mensagem, rotuloConfirmar, aoConfirmar, aoCancelar }: Props) {
  const id = useId();
  return (
    <div role="alertdialog" aria-labelledby={id} className="confirmacao">
      <p id={id}>{mensagem}</p>
      <div className="botoes">
        <button type="button" className="perigo" onClick={aoConfirmar}>
          {rotuloConfirmar}
        </button>
        <button type="button" className="secundario" autoFocus onClick={aoCancelar}>
          Cancelar
        </button>
      </div>
    </div>
  );
}
