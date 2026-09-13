// Registro componente-type → componente React. Único lugar que conoce el catálogo.
// Los renderers son COMPONENTES (se montan con <R/>): pueden usar hooks.
import type { OneOffAction, ComponentSpec } from "./types";

type Renderer = (args: { props: Record<string, unknown>; dispatch: (a: OneOffAction) => void }) => JSX.Element;

const RENDERERS: Record<string, Renderer> = {};
export function register(type: string, r: Renderer) { RENDERERS[type] = r; }
export function renderComponent(spec: ComponentSpec, dispatch: (a: OneOffAction) => void) {
  const R = RENDERERS[spec.componentType];
  if (!R) return <span>{'componente desconocido: ' + spec.componentType}</span>;
  // Tarjeta de info universal: cualquier componente del catálogo puede traer
  // props.info y el registry la muestra al cursor (y al foco de teclado).
  const info = spec.props?.info;
  return (
    <div className="muuk-hover">
      <R props={spec.props} dispatch={dispatch} />
      {typeof info === "string" && info !== "" && (
        <aside className="muuk-hovercard" role="tooltip">{info}</aside>
      )}
    </div>
  );
}
