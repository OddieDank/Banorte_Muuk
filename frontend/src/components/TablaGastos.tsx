// TablaGastos — filas con barra proporcional + total. Vista o dataRef remoto
// (privacidad: el LLM nunca ve transacciones crudas; el frontend las trae del API).
import { useEffect, useState } from "react";
import { register } from "../lib/registry";

interface Fila { concepto: string; monto: number; categoria: string; }

const API = import.meta.env.VITE_API_URL;
const formato = (n: number) => n.toLocaleString("es-MX", { style: "currency", currency: "MXN" });

register("TablaGastos", ({ props }: { props: Record<string, unknown> }) => {
  const [filas, setFilas] = useState<Fila[]>((props.filas as Fila[]) || []);

  useEffect(() => {
    if (!props.dataRef) return;
    // dataRef viene como "/api/transacciones"; el endpoint real es "/transacciones"
    const path = String(props.dataRef).replace(/^\/api/, "");
    const userId = localStorage.getItem("user_id");
    fetch(`${API}${path}?user_id=${userId}`)
      .then((r) => r.json())
      .then((rows: { categoria: string; monto: number }[]) =>
        setFilas(rows.map((r) => ({ concepto: r.categoria, monto: r.monto, categoria: r.categoria })))
      )
      .catch(() => {});
  }, [props.dataRef]);

  const max = Math.max(...filas.map((f) => f.monto), 1);
  const total = filas.reduce((s, f) => s + f.monto, 0);

  return (
    <div className="muuk-plan">
      <h3 className="muuk-title">{String(props.titulo ?? "Gastos")}</h3>
      {filas.map((f, i) => (
        <div key={i} className="muuk-fila"
             data-tip={total > 0 ? `${Math.round((f.monto / total) * 100)}% del total` : ""}>
          <div className="muuk-fila-info">
            <span>{f.concepto === f.categoria ? f.concepto : `${f.concepto} · ${f.categoria}`}</span>
            <b>{formato(f.monto)}</b>
          </div>
          <div className="muuk-barra">
            <div className="muuk-barra-fill" style={{ width: `${(f.monto / max) * 100}%` }} />
          </div>
        </div>
      ))}
      {filas.length > 1 && (
        <div className="muuk-fila muuk-total">
          <div className="muuk-fila-info">
            <span>Total</span>
            <b>{formato(total)}</b>
          </div>
        </div>
      )}
    </div>
  );
});
