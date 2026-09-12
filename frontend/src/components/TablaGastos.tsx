// TablaGastos — vista de filas o detalle remoto vía dataRef (privacidad:
// el LLM nunca ve las transacciones crudas; el frontend las trae del API).
import { useEffect, useState } from "react";
import { register } from "../a2ui/registry";

interface Fila { concepto: string; monto: number; categoria: string; }

const API = "http://localhost:8000";

register("TablaGastos", (props: Record<string, unknown>) => {
  const [filas, setFilas] = useState<Fila[]>((props.filas as Fila[]) || []);

  useEffect(() => {
    if (!props.dataRef) return;
    // dataRef viene como "/api/transacciones"; el endpoint real es "/transacciones"
    const path = String(props.dataRef).replace(/^\/api/, "");
    fetch(`${API}${path}`)
      .then((r) => r.json())
      .then((rows: { categoria: string; monto: number }[]) =>
        setFilas(rows.map((r) => ({ concepto: r.categoria, monto: r.monto, categoria: r.categoria })))
      )
      .catch(() => {});
  }, [props.dataRef]);

  return (
    <div className="muuk-plan">
      <h3 className="muuk-title">{String(props.titulo ?? "Gastos")}</h3>
      {filas.map((f, i) => (
        <div key={i} className="muuk-opcion">
          <span>{f.concepto} · {f.categoria}</span>
          <b>{f.monto.toLocaleString("es-MX", { style: "currency", currency: "MXN" })}</b>
        </div>
      ))}
    </div>
  );
});
