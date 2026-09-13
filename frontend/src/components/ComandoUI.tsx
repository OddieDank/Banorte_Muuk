// ComandoUI — comandos de la propia interfaz (modo oscuro, exportar PDF).
// El frontend los ejecuta localmente y registra la interacción igual.
import { useEffect } from "react";
import { register } from "../a2ui/registry";
import type { OneOffAction } from "../a2ui/types";

const ACCIONES: Record<string, { label: string; run: () => void }> = {
  modo_oscuro: { label: "Modo oscuro", run: () => document.body.classList.toggle("muuk-dark") },
  exportar_pdf: { label: "Exportar a PDF", run: () => window.print() },
};

register("ComandoUI", ({ props, dispatch }: { props: Record<string, unknown>; dispatch: (a: OneOffAction) => void }) => {
  const accion = String(props.accion ?? "");
  const def = ACCIONES[accion];

  useEffect(() => {
    def?.run();
    dispatch({ sessionId: "", componente: "ComandoUI", evento: accion, payload: { accion } as any });
  }, [accion]);

  return def ? (
    <span className="muuk-comando-chip">✓ {def.label}</span>
  ) : null;
});
