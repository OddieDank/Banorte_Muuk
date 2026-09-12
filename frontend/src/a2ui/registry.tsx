// Registro componente-type → componente React. Único lugar que conoce el catálogo.
// Los renderers son COMPONENTES (se montan con <R/>): pueden usar hooks.
import type { OneOffAction } from "./types";
import type { ComponentSpec } from "./types";

type Renderer = (args: { props: Record<string, unknown>; dispatch: (a: OneOffAction) => void }) => JSX.Element;

const RENDERERS: Record<string, Renderer> = {};
export function register(type: string, r: Renderer) { RENDERERS[type] = r; }
export function renderComponent(spec: ComponentSpec, dispatch: (a: OneOffAction) => void) {
  const R = RENDERERS[spec.componentType];
  return R ? <R props={spec.props} dispatch={dispatch} /> : <span>{'componente desconocido: ' + spec.componentType}</span>;
}
