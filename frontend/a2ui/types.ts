export interface ComponentSpec { componentId: string; componentType: string; props: Record<string, unknown>; }
export interface Surface { components: ComponentSpec[]; }
export type A2UIMessage = { type: string } & Record<string, unknown>;
export type OneOffAction = { sessionId: string; componente: string; evento: string; payload?: Record<string, unknown> };
