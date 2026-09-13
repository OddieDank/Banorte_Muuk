// Confirmacion — mensaje de cierre + detalles opcionales.
import { register } from "../lib/registry";

register("Confirmacion", ({ props }: { props: Record<string, unknown> }) => (
  <div className="muuk-plan">
    <h3 className="muuk-title">{String(props.mensaje ?? "Listo")}</h3>
    {props.detalles != null && (
      <pre className="muuk-detalles">{JSON.stringify(props.detalles, null, 2)}</pre>
    )}
  </div>
));
