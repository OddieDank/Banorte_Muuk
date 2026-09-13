// Adapter A2UI mínimo: paseSSE → acciones sobre state de surfaces.
import type { A2UIMessage, Surface, ComponentSpec } from "./types";

export function applyMessage(surfaces: Record<string, Surface>, msg: A2UIMessage): Record<string, Surface> {
  const m = msg as any;
  switch (m.type) {
    case "createSurface":
      return { ...surfaces, [m.surfaceId]: { ...surfaces[m.surfaceId], components: [] } };
    case "surfaceUpdate": {
      const comps = m.components.map((c: any) => //
        ({ componentId: c.componentId, componentType: c.componentType, props: c.props }));
      return { ...surfaces, [m.surfaceId]:
        { ...surfaces[m.surfaceId], components: [...(surfaces[m.surfaceId]?.components ?? []), ...comps] } };
    }
    case "deleteSurface": {
      const { [m.surfaceId]: _, ...rest } = surfaces;
      return rest;
    }
    case "dataModelUpdate":
      return surfaces; // metadata se maneja aparte del registry
    default:
      return surfaces;
  }
}
