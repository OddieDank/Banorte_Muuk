// Registro componente-type → componente React. Único lugar que conoce el catálogo.
import type { OneOffAction } from "./types";
import type { ComponentSpec } from "./types";

type Renderer = (props: Record<string, unknown>, dispatch: (a: OneOffAction) => void) => JSX.Element;

const RENDERERS: Record<string, Renderer> = {};
export function register(type: string, r: Renderer) { RENDERERS[type] = r; }
export function renderComponent(spec: ComponentSpec, dispatch: (a: OneOffAction) => void) {
  const r = RENDERERS[spec.componentType];
  return r ? r(spec.props, dispatch) : <span>{'componente desconocido: ' + spec.componentType}</span>;
}
