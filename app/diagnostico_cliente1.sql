-- ============================================================================
-- Diagnostico puntual: cliente 1 (Juan Taller)
-- Corré las 3 consultas y pegame los 3 resultados (indicá cuál es cuál).
-- Si usás pgAdmin/DBeaver: correlas una por una y copiá cada resultado.
-- ============================================================================

-- 1a) Valor cacheado actual (el que devuelve la API / ve el frontend)
SELECT id, nombre, saldo_favor AS saldo_favor_cacheado
FROM clientes
WHERE id = 1;

-- 1b) Resumen por tipo de movimiento: cuántos hay, cuánto suman, y hasta cuándo
SELECT
    tipo,
    COUNT(*)   AS cantidad,
    SUM(monto) AS suma_monto,
    MIN(fecha) AS primera_fecha,
    MAX(fecha) AS ultima_fecha
FROM movimientos_cliente
WHERE cliente_id = 1
GROUP BY tipo
ORDER BY tipo;

-- 1e) Detalle cronológico completo de movimientos del cliente
SELECT
    id,
    tipo,
    monto,
    venta_id,
    pago_id,
    fecha,
    observaciones
FROM movimientos_cliente
WHERE cliente_id = 1
ORDER BY fecha, id;
