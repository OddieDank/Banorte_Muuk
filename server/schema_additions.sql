-- Cambios sugeridos al esquema principal (complemento; transaccion ya la cubre el
-- script del compañero de BD con su hypertable + continuous aggregate).

-- 1. Montos por producto contratado (tarjeta, débito, préstamo)
ALTER TABLE usuario_producto ADD COLUMN saldo_actual NUMERIC(12,2) DEFAULT 0;
ALTER TABLE usuario_producto ADD COLUMN deuda_actual NUMERIC(12,2) DEFAULT 0;

-- 2. Planes aplicados (persistencia de la acción de escritura del agente)
CREATE TABLE plan_pago (
    plan_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id        UUID NOT NULL REFERENCES usuario(user_id) ON DELETE CASCADE,
    interaccion_id UUID,
    interaccion_ts TIMESTAMPTZ,
    meses          INT NOT NULL,
    pago_mensual   NUMERIC(12,2) NOT NULL,
    cat            NUMERIC(5,2) NOT NULL,
    monto_original NUMERIC(12,2) NOT NULL,
    estado         TEXT DEFAULT 'activo',
    creado_ts      TIMESTAMPTZ NOT NULL DEFAULT now(),
    FOREIGN KEY (interaccion_id, interaccion_ts) REFERENCES interaccion(interaccion_id, "timestamp")
);

-- Los grants para mcp_agent viven en transaccion.sql (se ejecuta después de este
-- script para que plan_pago ya exista).
