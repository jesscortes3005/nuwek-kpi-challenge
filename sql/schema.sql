-- Referencia del esquema. El importador lo crea automáticamente con SQLAlchemy;
-- este archivo equivale a ese esquema (sqlite3 ventas.db < sql/schema.sql).
CREATE TABLE IF NOT EXISTS ventas (
    id_venta  TEXT PRIMARY KEY,
    fecha     DATE NOT NULL,                 -- 'YYYY-MM-DD'
    vendedor  TEXT,                          -- puede ser NULL (el reto conserva estas filas)
    region    TEXT NOT NULL,
    producto  TEXT,
    monto     NUMERIC(12,2) NOT NULL CHECK (monto >= 0),
    estatus   TEXT NOT NULL CHECK (estatus IN ('cerrada','abierta','cancelada'))
);

-- Coincide con el patrón de consulta: WHERE estatus = 'cerrada' AND fecha BETWEEN ...
CREATE INDEX IF NOT EXISTS idx_ventas_estatus_fecha ON ventas (estatus, fecha);
