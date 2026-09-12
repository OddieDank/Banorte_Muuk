// PlanDePago — componente accionable genérico. Sin dependencia de UI lib.
import { register } from "../a2ui/registry";
import type { OneOffAction } from "../a2ui/types";

interface Opcion { meses: number; pago_mensual: number; cat: number; }

register("PlanDePago", ({ props, dispatch }: { props: Record<string, unknown>; dispatch: (a: OneOffAction) => void }) => {
  const opciones = (props.opciones as Opcion[]) || [];
  return (
    <div className="muuk-plan">
      <h3 className="muuk-title">{String(props.mensaje ?? "Plan de pago")}</h3>
      {opciones.map((o, i) => (
        <div key={i} className="muuk-opcion">
          <span>Mensual: <b>{formato(o.pago_mensual)}</b> | {o.meses} meses · CAT {o.cat}%</span>
          <button onClick={() =>
            dispatch({ sessionId: "", componente: "PlanDePago", evento: "aplicar_plan", payload: o as any })
          }>{String(props.cta || "Aplicar plan")}</button>
        </div>
      ))}
    </div>
  );
});

function formato(n: number) {
  return n.toLocaleString("es-MX", { style: "currency", currency: "MXN" });
}
