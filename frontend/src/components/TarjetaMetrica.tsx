// TarjetaMetrica — número grande tipo dashboard. Clic registra interés en la métrica.
import { register } from "../lib/registry";
import type { OneOffAction } from "../lib/registry-types";

register("TarjetaMetrica", ({ props, dispatch }: { props: Record<string, unknown>; dispatch: (a: OneOffAction) => void }) => (
  <div
    className="muuk-plan muuk-metrica"
    onClick={() =>
      dispatch({ sessionId: "", componente: "TarjetaMetrica", evento: "ver_metrica",
        payload: { titulo: props.titulo, valor: props.valor } as any })
    }
  >
    <span className="muuk-metrica-titulo">{String(props.titulo ?? "")}</span>
    <span className="muuk-metrica-valor">{String(props.valor ?? "")}</span>
    {props.subtitulo != null && <span className="muuk-metrica-sub">{String(props.subtitulo)}</span>}
  </div>
));
