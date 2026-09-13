// ProgresoMeta — barra de progreso hacia una meta de ahorro.
// Clic dispatch("ver_meta") → /action (memoria adaptativa).
import { register } from "../a2ui/registry";
import type { OneOffAction } from "../a2ui/types";

const formato = (n: number) => n.toLocaleString("es-MX", { style: "currency", currency: "MXN", maximumFractionDigits: 0 });

register("ProgresoMeta", ({ props, dispatch }: { props: Record<string, unknown>; dispatch: (a: OneOffAction) => void }) => {
  const actual = Number(props.actual ?? 0);
  const meta = Number(props.meta ?? 0);
  const pct = meta > 0 ? Math.min(100, Math.round((actual / meta) * 100)) : 0;

  return (
    <div
      className="muuk-plan muuk-progreso"
      onClick={() =>
        dispatch({ sessionId: "", componente: "ProgresoMeta", evento: "ver_meta",
          payload: { titulo: props.titulo, actual, meta } as any })
      }
    >
      <span className="muuk-metrica-titulo">{String(props.titulo ?? "Meta")}</span>
      <span className="muuk-progreso-cifra">{pct}%</span>
      <div className="muuk-progreso-pista" role="progressbar" aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100}>
        <div className="muuk-progreso-barra" style={{ width: `${pct}%` }} />
      </div>
      <span className="muuk-metrica-sub">{formato(actual)} de {formato(meta)}</span>
    </div>
  );
});
