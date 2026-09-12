-- ============================================================
-- Transacciones: hypertable + agregación continua + permisos
-- (corregido: typo final, grants completos para mcp_agent)
-- ============================================================

-- ------------------------------------------------------------
-- 1. Tabla base (hypertable — fecha debe estar en la PK)
-- ------------------------------------------------------------
CREATE TABLE transaccion (
    transaccion_id    UUID DEFAULT gen_random_uuid(),
    user_product_id   UUID NOT NULL REFERENCES usuario_producto(user_product_id) ON DELETE CASCADE,
    fecha             TIMESTAMPTZ NOT NULL DEFAULT now(),
    categoria         TEXT NOT NULL,
    monto             NUMERIC(12,2) NOT NULL,
    tipo              TEXT NOT NULL CHECK (tipo IN ('cargo','abono')),
    PRIMARY KEY (transaccion_id, fecha)
);
SELECT create_hypertable('transaccion', by_range('fecha'));

-- ------------------------------------------------------------
-- 2. Agregación continua: resumen mensual por cuenta/categoría
-- ------------------------------------------------------------
CREATE MATERIALIZED VIEW transaccion_resumen
WITH (timescaledb.continuous) AS
SELECT
    user_product_id,
    time_bucket('1 month', fecha) AS mes,
    categoria,
    SUM(monto) FILTER (WHERE tipo = 'cargo')  AS total_gastado,
    SUM(monto) FILTER (WHERE tipo = 'abono')  AS total_ingresos,
    COUNT(*)                                   AS num_movimientos
FROM transaccion
GROUP BY user_product_id, time_bucket('1 month', fecha), categoria;

-- ------------------------------------------------------------
-- 3. Política de refresco automático (cada hora, ventana de 3 meses)
-- ------------------------------------------------------------
SELECT add_continuous_aggregate_policy('transaccion_resumen',
    start_offset      => INTERVAL '3 months',
    end_offset        => INTERVAL '1 hour',
    schedule_interval  => INTERVAL '1 hour'
);

-- ------------------------------------------------------------
-- 4. Rol limitado para el agente (servidor MCP)
-- ------------------------------------------------------------
CREATE ROLE mcp_agent LOGIN PASSWORD 'CAMBIA_ESTA_CONTRASENA';

-- ------------------------------------------------------------
-- 5. Permisos: nunca la tabla cruda, solo el agregado
-- ------------------------------------------------------------
REVOKE ALL ON transaccion FROM mcp_agent;      -- explícito, por si acaso
GRANT SELECT ON transaccion_resumen TO mcp_agent;

-- Catálogos y perfiles: solo lectura
GRANT SELECT ON usuario, perfil_financiero, producto, usuario_producto,
                sesion, intencion, componente_ui
    TO mcp_agent;

-- Escritura del loop (interacciones, UI generada, acciones)
GRANT SELECT, INSERT ON interaccion, ui_generada, componente_generada, accion_ui
    TO mcp_agent;

-- Grants que faltaban (sin estos el loop truena):
GRANT INSERT ON sesion TO mcp_agent;                          -- crear sesiones
GRANT SELECT, INSERT, UPDATE ON preferencia_ui TO mcp_agent;  -- upsert de aprendizaje
GRANT INSERT ON plan_pago TO mcp_agent;                       -- aplicar_plan
