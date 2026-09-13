// GraficaLinea — tendencia por periodo en SVG propio, sin librerías.
// Puntos y etiquetas clicables: dispatch("ver_punto") → /action (memoria adaptativa).
import { useState } from "react";
import { register } from "../a2ui/registry";
import type { OneOffAction } from "../a2ui/types";

interface Punto { etiqueta: string; valor: number; }

const formato = (n: number) => n.toLocaleString("es-MX", { style: "currency", currency: "MXN", maximumFractionDigits: 0 });

register("GraficaLinea", ({ props, dispatch }: { props: Record<string, unknown>; dispatch: (a: OneOffAction) => void }) => {
  const puntos = (props.puntos as Punto[]) || [];
  const [sel, setSel] = useState<number | null>(null);
  if (puntos.length < 2) return null;

  const max = Math.max(...puntos.map((p) => p.valor)) || 1;
  const x = (i: number) => 8 + (i * 84) / (puntos.length - 1);
  const y = (v: number) => 44 - (v / max) * 36;
  const path = puntos.map((p, i) => `${i === 0 ? "M" : "L"}${x(i)},${y(p.valor)}`).join(" ");

  const elegir = (i: number) => {
    setSel(i);
    dispatch({ sessionId: "", componente: "GraficaLinea", evento: "ver_punto",
      payload: { etiqueta: puntos[i].etiqueta, valor: puntos[i].valor } as any });
  };

  return (
    <div className="muuk-plan muuk-chart">
      <h3 className="muuk-title">{String(props.titulo ?? "Tendencia")}</h3>
      <svg viewBox="0 0 100 50" className="muuk-linea" role="img">
        {[0.25, 0.5, 0.75].map((f) => (
          <line key={f} x1="8" x2="92" y1={44 - f * 36} y2={44 - f * 36} className="muuk-linea-grid" />
        ))}
        <path d={path} fill="none" className="muuk-linea-path" />
        {puntos.map((p, i) => (
          <g key={i} onClick={() => elegir(i)} style={{ cursor: "pointer" }}>
            <title>{`${p.etiqueta}: ${formato(p.valor)}`}</title>
            <circle cx={x(i)} cy={y(p.valor)} r={sel === i ? 2.2 : 1.5}
              className={sel === i ? "muuk-linea-pt activa" : "muuk-linea-pt"} />
            <text x={x(i)} y={y(p.valor) - 3} textAnchor="middle" className="muuk-linea-val">
              {sel === i ? formato(p.valor) : ""}
            </text>
            <text x={x(i)} y={49} textAnchor="middle" className="muuk-linea-etq">{p.etiqueta}</text>
          </g>
        ))}
      </svg>
    </div>
  );
});
