"""Capa de datos de Muuk — Tiger Data (PostgreSQL + TimescaleDB).

Esquema: ver ../docs/ o el script SQL del compañero de BD.
Fallback: sin DATABASE_URL, usa SQLite local con interfaz idéntica (dev sin red).
"""

import json
import os
import sqlite3
from contextlib import closing

DATABASE_URL = os.getenv("DATABASE_URL")
_USE_PG = bool(DATABASE_URL)

if _USE_PG:
    import psycopg2
    import psycopg2.extras


def _conn():
    if _USE_PG:
        return psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
    conn = sqlite3.connect("muuk.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def _q(sql: str, params: tuple = ()):
    """Ejecuta query y regresa filas como dicts."""
    with closing(_conn()) as conn:
        cur = conn.cursor()
        cur.execute(sql, params)
        rows = cur.fetchall()
        conn.commit()
        return [dict(r) for r in rows]


def _q1(sql: str, params: tuple = ()):
    rows = _q(sql, params)
    return rows[0] if rows else None


def _insert(sql: str, params: tuple = ()):
    with closing(_conn()) as conn:
        cur = conn.cursor()
        cur.execute(sql, params)
        conn.commit()
        return cur.lastrowid if not _USE_PG else None


# ── Usuario y perfil ──────────────────────────────────────────────────────

def get_usuario(user_id: str) -> dict | None:
    if _USE_PG:
        return _q1("SELECT * FROM usuario WHERE user_id = %s", (user_id,))
    return _q1("SELECT * FROM usuario WHERE user_id = ?", (user_id,))


def get_perfil_financiero(user_id: str) -> dict | None:
    if _USE_PG:
        return _q1("SELECT * FROM perfil_financiero WHERE user_id = %s", (user_id,))
    return _q1("SELECT * FROM perfil_financiero WHERE user_id = ?", (user_id,))


def get_productos_usuario(user_id: str) -> list[dict]:
    sql = """
        SELECT up.*, p.nombre, p.tipo, p.descripcion
        FROM usuario_producto up
        JOIN producto p ON p.product_id = up.product_id
        WHERE up.user_id = %s
    """ if _USE_PG else """
        SELECT up.*, p.nombre, p.tipo, p.descripcion
        FROM usuario_producto up
        JOIN producto p ON p.product_id = up.product_id
        WHERE up.user_id = ?
    """
    return _q(sql, (user_id,))


def get_resumen_gastos(user_id: str, meses: int = 3) -> list[dict]:
    """Agregados por categoría/mes. ESTO es lo que ve el agente (privacidad:
    nunca la tabla cruda `transaccion`, solo el continuous aggregate)."""
    if _USE_PG:
        return _q(
            """SELECT r.mes, r.categoria, r.total_gastado, r.total_ingresos, r.num_movimientos
               FROM transaccion_resumen r
               JOIN usuario_producto up ON up.user_product_id = r.user_product_id
               WHERE up.user_id = %s
               ORDER BY r.mes DESC""",
            (user_id,),
        )
    return _q(
        """SELECT strftime('%Y-%m', t.fecha) AS mes, t.categoria,
                  SUM(CASE WHEN t.tipo='cargo' THEN t.monto END) AS total_gastado,
                  SUM(CASE WHEN t.tipo='abono' THEN t.monto END) AS total_ingresos,
                  COUNT(*) AS num_movimientos
           FROM transaccion t
           JOIN usuario_producto up ON up.user_product_id = t.user_product_id
           WHERE up.user_id = ?
           GROUP BY mes, t.categoria ORDER BY mes DESC""",
        (user_id,),
    )


def get_transacciones(user_id: str, limit: int = 20) -> list[dict]:
    """Detalle crudo. SOLO para el endpoint del frontend (rol de aplicación),
    NUNCA se expone como tool MCP del agente."""
    sql = """
        SELECT t.categoria, t.monto, t.tipo, t.fecha
        FROM transaccion t
        JOIN usuario_producto up ON up.user_product_id = t.user_product_id
        WHERE up.user_id = %s
        ORDER BY t.fecha DESC LIMIT %s
    """ if _USE_PG else """
        SELECT t.categoria, t.monto, t.tipo, t.fecha
        FROM transaccion t
        JOIN usuario_producto up ON up.user_product_id = t.user_product_id
        WHERE up.user_id = ?
        ORDER BY t.fecha DESC LIMIT ?
    """
    return _q(sql, (user_id, limit))


# ── Sesiones e interacciones ──────────────────────────────────────────────

def crear_sesion(user_id: str, canal: str = "web") -> str:
    if _USE_PG:
        row = _q1(
            "INSERT INTO sesion (user_id, canal) VALUES (%s, %s) RETURNING sesion_id",
            (user_id, canal),
        )
        return str(row["sesion_id"])
    # SQLite fallback
    _insert("INSERT INTO sesion (user_id, canal) VALUES (?, ?)", (user_id, canal))
    return user_id  # simplificado para dev


def registrar_interaccion(sesion_id: str, intencion_id: str | None, tipo: str, contenido: str) -> dict:
    if _USE_PG:
        row = _q1(
            """INSERT INTO interaccion (sesion_id, intencion_id, tipo, contenido)
               VALUES (%s, %s, %s, %s) RETURNING interaccion_id, "timestamp" """,
            (sesion_id, intencion_id, tipo, contenido),
        )
        return {"interaccion_id": str(row["interaccion_id"]), "timestamp": str(row["timestamp"])}
    _insert(
        "INSERT INTO interaccion (sesion_id, intencion_id, tipo, contenido) VALUES (?, ?, ?, ?)",
        (sesion_id, intencion_id, tipo, contenido),
    )
    return {"ok": True}


def get_resumen_interacciones(sesion_id: str, limit: int = 20) -> list[dict]:
    sql = """
        SELECT tipo, contenido, "timestamp"
        FROM interaccion WHERE sesion_id = %s
        ORDER BY "timestamp" DESC LIMIT %s
    """ if _USE_PG else """
        SELECT tipo, contenido, timestamp
        FROM interaccion WHERE sesion_id = ?
        ORDER BY timestamp DESC LIMIT ?
    """
    return _q(sql, (sesion_id, limit))


# ── UI generada y componentes ─────────────────────────────────────────────

def registrar_ui_generada(interaccion_id: str, interaccion_ts: str, version: int = 1) -> str:
    if _USE_PG:
        row = _q1(
            "INSERT INTO ui_generada (interaccion_id, interaccion_ts, version) VALUES (%s, %s, %s) RETURNING ui_generada_id",
            (interaccion_id, interaccion_ts, version),
        )
        return str(row["ui_generada_id"])
    return "dev"


def registrar_componente_generada(ui_generada_id: str, componente_id: str, orden: int = 0, tamano: str = "md", visible: bool = True) -> str:
    if _USE_PG:
        row = _q1(
            "INSERT INTO componente_generada (ui_generada_id, componente_id, orden, tamano, visible) VALUES (%s, %s, %s, %s, %s) RETURNING componente_gen_id",
            (ui_generada_id, componente_id, orden, tamano, visible),
        )
        return str(row["componente_gen_id"])
    return "dev"


def registrar_accion_ui(componente_gen_id: str, tipo_accion: str, valor: str, success: bool) -> dict:
    if _USE_PG:
        _q(
            "INSERT INTO accion_ui (componente_gen_id, tipo_accion, valor, success) VALUES (%s, %s, %s, %s)",
            (componente_gen_id, tipo_accion, valor, success),
        )
    return {"ok": True}


# ── Preferencias (aprendizaje) ────────────────────────────────────────────

def get_preferencias(user_id: str, intencion_id: str | None = None) -> list[dict]:
    if intencion_id:
        sql = "SELECT * FROM preferencia_ui WHERE user_id = %s AND intencion_id = %s" if _USE_PG else \
              "SELECT * FROM preferencia_ui WHERE user_id = ? AND intencion_id = ?"
        return _q(sql, (user_id, intencion_id))
    sql = "SELECT * FROM preferencia_ui WHERE user_id = %s" if _USE_PG else \
          "SELECT * FROM preferencia_ui WHERE user_id = ?"
    return _q(sql, (user_id,))


def actualizar_preferencia(user_id: str, intencion_id: str, componente_id: str, success: bool):
    """Upsert: incrementa usage_count, success_count, recalcula score."""
    if _USE_PG:
        _q(
            """INSERT INTO preferencia_ui (user_id, intencion_id, componente_id, usage_count, success_count, score, ultimo_uso)
               VALUES (%s, %s, %s, 1, %s, %s, now())
               ON CONFLICT (user_id, intencion_id, componente_id)
               DO UPDATE SET
                 usage_count = preferencia_ui.usage_count + 1,
                 success_count = preferencia_ui.success_count + %s,
                 score = (preferencia_ui.success_count + %s)::numeric / (preferencia_ui.usage_count + 1),
                 ultimo_uso = now()""",
            (user_id, intencion_id, componente_id, 1 if success else 0, 1 if success else 0, 1 if success else 0, 1 if success else 0),
        )


# ── Planes de pago ────────────────────────────────────────────────────────

def aplicar_plan(user_id: str, meses: int, pago_mensual: float, cat: float, monto_original: float, interaccion_id: str | None = None, interaccion_ts: str | None = None) -> dict:
    if _USE_PG:
        row = _q1(
            """INSERT INTO plan_pago (user_id, interaccion_id, interaccion_ts, meses, pago_mensual, cat, monto_original)
               VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING plan_id""",
            (user_id, interaccion_id, interaccion_ts, meses, pago_mensual, cat, monto_original),
        )
        return {"plan_id": str(row["plan_id"]), "ok": True}
    return {"plan_id": "dev", "ok": True}


# ── Simulación (pura, sin DB) ─────────────────────────────────────────────

def simular_plan_pago(deuda: float, meses: int, cat: float) -> dict:
    tasa = cat / 100 / 12
    pago = deuda * (tasa * (1 + tasa) ** meses) / ((1 + tasa) ** meses - 1)
    return {"meses": meses, "pago_mensual": round(pago, 2), "cat": cat, "total": round(pago * meses, 2)}


# ── SQLite fallback init (solo dev) ───────────────────────────────────────

def _init_sqlite():
    if _USE_PG:
        return
    with closing(_conn()) as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS usuario (user_id TEXT PRIMARY KEY, nombre TEXT, edad_rango TEXT, ocupacion TEXT);
            CREATE TABLE IF NOT EXISTS perfil_financiero (user_id TEXT PRIMARY KEY, ingreso_rango TEXT, ahorro_nivel TEXT, deuda_nivel TEXT, meta_financiera TEXT);
            CREATE TABLE IF NOT EXISTS producto (product_id TEXT PRIMARY KEY, nombre TEXT, tipo TEXT, descripcion TEXT);
            CREATE TABLE IF NOT EXISTS usuario_producto (user_product_id TEXT PRIMARY KEY, user_id TEXT, product_id TEXT, estado TEXT, saldo_actual REAL DEFAULT 0, deuda_actual REAL DEFAULT 0);
            CREATE TABLE IF NOT EXISTS sesion (sesion_id TEXT PRIMARY KEY, user_id TEXT, canal TEXT);
            CREATE TABLE IF NOT EXISTS interaccion (sesion_id TEXT, intencion_id TEXT, tipo TEXT, contenido TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP);
            CREATE TABLE IF NOT EXISTS transaccion (transaccion_id TEXT, user_product_id TEXT, fecha DATETIME DEFAULT CURRENT_TIMESTAMP, categoria TEXT, monto REAL, tipo TEXT);
        """)
        if conn.execute("SELECT COUNT(*) FROM usuario").fetchone()[0] == 0:
            conn.executemany("INSERT INTO usuario VALUES (?, ?, ?, ?)", [
                ("u1", "Ana Ruiz", "25-34", "empleada"),
                ("u2", "Luis Torres", "35-44", "independiente"),
            ])
            conn.executemany("INSERT INTO perfil_financiero VALUES (?, ?, ?, ?, ?)", [
                ("u1", "20k-40k", "medium", "high", "pagar deuda"),
                ("u2", "40k-60k", "high", "low", "invertir"),
            ])
            conn.executemany("INSERT INTO producto VALUES (?, ?, ?, ?)", [
                ("p1", "Tarjeta de Crédito Clásica", "credito", "Tarjeta de crédito Banorte"),
                ("p2", "Cuenta de Débito", "debito", "Cuenta de débito y nómina"),
                ("p3", "Préstamo Personal", "prestamo", "Préstamo personal a tasa fija"),
            ])
            conn.executemany("INSERT INTO usuario_producto VALUES (?, ?, ?, ?, ?, ?)", [
                ("up1", "u1", "p1", "activo", 0, 18400),       # tarjeta con deuda
                ("up2", "u1", "p2", "activo", 42500, 0),        # débito con saldo
                ("up3", "u2", "p1", "activo", 0, 5100),         # tarjeta con deuda menor
                ("up4", "u2", "p3", "activo", 0, 35000),        # préstamo activo
            ])
            conn.executemany("INSERT INTO transaccion (user_product_id, categoria, monto, tipo) VALUES (?, ?, ?, ?)", [
                ("up2", "alimentacion", 1250, "cargo"),
                ("up2", "transporte", 800, "cargo"),
                ("up2", "entretenimiento", 299, "cargo"),
                ("up2", "ingreso", 25000, "abono"),
                ("up1", "alimentacion", 640, "cargo"),
            ])
        conn.commit()


_init_sqlite()
