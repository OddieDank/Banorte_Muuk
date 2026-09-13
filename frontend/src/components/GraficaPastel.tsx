// GraficaPastel — donut SVG propio. Cada rebanada y leyenda es clicable:
// dispatch("ver_categoria") → /action → interaction_log (memoria adaptativa).
import { useState } from "react";
import { register } from "../a2ui/registry";
import type { OneOffAction } from "../a2ui/types";

interface Segmento { etiqueta: string; valor: number; }

const PALETA = ["#b5121b", "#eb0029", "#5b6770", "#d4a017", "#3a7d44", "#6b4fa1", "#0f7b8a", "#c25e00"];
const formato = (n: number) => n.toLocaleString("es-MX", { style: "currency", currency: "MXN", maximumFractionDigits: 0 });

register("GraficaPastel", ({ props, dispatch }: { props: Record<string, unknown>; dispatch: (a: OneOffAction) => void }) => {
  const segmentos = (props.segmentos as Segmento[]) || [];
  const total = segmentos.reduce((s, x) => s + x.valor, 0) || 1;
  const [sel, setSel] = useState<number | null>(null);

  let offset = 25; // empieza arriba
  const rebanadas = segmentos.map((s, i) => {
    const pct = (s.valor / total) * 100;
    const r = { ...s, pct, offset, color: PALETA[i % PALETA.length] };
    offset -= pct;
    return r;
  });

  const elegir = (i: number) => {
    setSel(i);
    dispatch({ sessionId: "", componente: "GraficaPastel", evento: "ver_categoria",
      payload: { categoria: segmentos[i].etiqueta, valor: segmentos[i].valor } as any });
  };

  return (
    <div className="muuk-plan muuk-chart">
      <h3 className="muuk-title">{String(props.titulo ?? "Distribución")}</h3>
      <div className="muuk-donut-wrap">
        <svg viewBox="0 0 42 42" className="muuk-donut">
          <circle cx="21" cy="21" r="15.9155" fill="none" stroke="#f0f0f0" strokeWidth="6" />
          {rebanadas.map((r, i) => (
            <circle
              key={i}
              cx="21" cy="21" r="15.9155" fill="none"
              stroke={r.color}
              strokeWidth={sel === i ? 7.5 : 6}
              strokeDasharray={`${r.pct} ${100 - r.pct}`}
              strokeDashoffset={r.offset}
              onClick={() => elegir(i)}
              style={{ cursor: "pointer", transition: "stroke-width 0.15s" }}
            />
          ))}
          <text x="21" y="20" textAnchor="middle" className="muuk-donut-total">{formato(total)}</text>
          <text x="21" y="25" textAnchor="middle" className="muuk-donut-label">
            {sel != null ? rebanadas[sel].etiqueta : "total"}
          </text>
        </svg>
        <ul className="muuk-leyenda">
          {rebanadas.map((r, i) => (
            <li key={i} onClick={() => elegir(i)} className={sel === i ? "activa" : ""}>
              <span className="muuk-dot" style={{ background: r.color }} />
              <span className="muuk-leyenda-nombre">{r.etiqueta}</span>
              <b>{formato(r.valor)}</b>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
});
