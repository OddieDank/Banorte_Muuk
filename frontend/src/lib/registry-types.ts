// Único tipo compartido por los componentes del catálogo (una acción → POST /action).
export type OneOffAction = { sessionId?: string; componente: string; evento: string; payload?: Record<string, unknown> };
