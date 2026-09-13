// GraficaBarras — barras verticales CSS. Cada barra es clicable:
// dispatch("ver_periodo") → /action → interaction_log.
import { useState } from "react";
import { register } from "../lib/registry";
import type { OneOffAction } from "../lib/registry-types";

interface Barra { etiqueta: string; valor: number; }

const formato = (n: number) => n.toLocaleString("es-MX", { style: "currency", currency: "MXN", maximumFractionDigits: 0 });

register("GraficaBarras", ({ props, dispatch }: { props: Record<string, unknown>; dispatch: (a: OneOffAction) => void }) => {
  const barras = (props.barras as Barra[]) || [];
  const max = Math.max(...barras.map((b) => b.valor), 1);
  const [sel, setSel] = useState<number | null>(null);

  const elegir = (i: number) => {
    setSel(i);
    dispatch({ sessionId: "", componente: "GraficaBarras", evento: "ver_periodo",
      payload: { periodo: barras[i].etiqueta, valor: barras[i].valor } as any });
  };

  return (
    <div className="muuk-plan muuk-chart">
      <h3 className="muuk-title">{String(props.titulo ?? "Por periodo")}</h3>
      <div className="muuk-barras">
        {barras.map((b, i) => (
          <button key={i} type="button" className="muuk-barra-col" onClick={() => elegir(i)}
                  data-tip={`${b.etiqueta}: ${formato(b.valor)}`}>
            <span className="muuk-barra-valor">{sel === i ? formato(b.valor) : ""}</span>
            <span
              className={`muuk-barra-rect${sel === i ? " activa" : ""}`}
              style={{ height: `${(b.valor / max) * 100}%` }}
            />
            <span className="muuk-barra-etq">{b.etiqueta}</span>
          </button>
        ))}
      </div>
    </div>
  );
});
