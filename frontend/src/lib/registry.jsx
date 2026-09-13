// Registro componente-type → componente React. Único lugar que conoce el catálogo.
// Los renderers son COMPONENTES (se montan con <R/>): pueden usar hooks.
// (Movido de src/a2ui — el subset propio se sustituyó por @copilotkit/a2ui-renderer.)
const RENDERERS = {};
export function register(type, r) { RENDERERS[type] = r; }
export function renderComponent(spec, dispatch) {
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
