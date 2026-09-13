// PlanDePago — opciones de reestructura seleccionables + CTA único.
// El dispatch lleva la opción elegida + monto_original (escritura real en BD).
import { useState } from "react";
import { register } from "../a2ui/registry";
import type { OneOffAction } from "../a2ui/types";

interface Opcion { meses: number; pago_mensual: number; cat: number; total?: number; }

register("PlanDePago", ({ props, dispatch }: { props: Record<string, unknown>; dispatch: (a: OneOffAction) => void }) => {
  const opciones = (props.opciones as Opcion[]) || [];
  const monto = Number(props.monto_original ?? 0);
  const [sel, setSel] = useState(0);
  const op = opciones[sel];

  return (
    <div className="muuk-plan">
      <h3 className="muuk-title">{String(props.mensaje ?? "Plan de pago")}</h3>
      {monto > 0 && <p className="muuk-saldo">Saldo a reestructurar: <b>{formato(monto)}</b></p>}

      <div className="muuk-opciones">
        {opciones.map((o, i) => (
          <button
            key={i}
            type="button"
            className={`muuk-opcion-card${i === sel ? " seleccionada" : ""}`}
            onClick={() => setSel(i)}
            data-tip={o.total
              ? `A ${o.meses} meses pagas ${formato(o.total)} en total (CAT ${o.cat}%)`
              : `Plazo de ${o.meses} meses con CAT ${o.cat}%`}
          >
            <span className="muuk-opcion-meses">{o.meses} meses</span>
            <span className="muuk-opcion-pago">{formato(o.pago_mensual)}<small>/mes</small></span>
            <span className="muuk-opcion-cat">CAT {o.cat}%{o.total ? ` · total ${formato(o.total)}` : ""}</span>
          </button>
        ))}
      </div>

      {op && (
        <button
          className="muuk-cta"
          onClick={() =>
            dispatch({ sessionId: "", componente: "PlanDePago", evento: "aplicar_plan",
              payload: { ...op, monto_original: monto } as any })
          }
        >
          {String(props.cta || "Aplicar plan")} · {op.meses} meses
        </button>
      )}
    </div>
  );
});

function formato(n: number) {
  return n.toLocaleString("es-MX", { style: "currency", currency: "MXN" });
}
