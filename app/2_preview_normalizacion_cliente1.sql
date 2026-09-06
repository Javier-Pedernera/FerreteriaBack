-- ============================================================================
-- PREVIEW (solo lectura, no cambia nada) — piloto cliente 1 (Juan Taller)
-- Muestra, venta por venta, qué movimientos VENTA tiene hoy, cuánto suman,
-- y qué se va a insertar en su lugar. Revisalo antes de correr el script
-- de corrección real (3_normalizar_cliente1.sql).
-- ============================================================================

-- 1) Ventas de Juan Taller con saldo pendiente real, y su estado actual
SELECT
    v.id AS venta_id,
    v.total,
    v.pagado,
    (v.total - v.pagado) AS saldo_pendiente_real,
    COALESCE(m.suma_actual, 0) AS suma_movimientos_actual,
    COALESCE(m.cantidad_movimientos, 0) AS cantidad_movimientos_actual,
    -(v.total - v.pagado) AS monto_correcto_que_deberia_quedar,
    CASE
        WHEN COALESCE(m.suma_actual, 0) = -(v.total - v.pagado) THEN 'OK - no se toca'
        WHEN m.suma_actual IS NULL THEN 'HUERFANA - se inserta movimiento nuevo'
        ELSE 'MAL - se reemplaza por un movimiento limpio'
    END AS accion
FROM ventas v
LEFT JOIN (
    SELECT venta_id, SUM(monto) AS suma_actual, COUNT(*) AS cantidad_movimientos
    FROM movimientos_cliente
    WHERE tipo = 'VENTA'
    GROUP BY venta_id
) m ON m.venta_id = v.id
LEFT JOIN status s ON s.id = v.estado_id
WHERE v.cliente_id = 1
  AND (s.code IS NULL OR s.code <> 'deleted')
  AND (v.total - v.pagado) <> 0
ORDER BY v.id;

-- 2) Los movimientos VENTA puntuales que se van a borrar (para las "MAL")
SELECT mc.*
FROM movimientos_cliente mc
JOIN ventas v ON v.id = mc.venta_id
LEFT JOIN status s ON s.id = v.estado_id
WHERE v.cliente_id = 1
  AND mc.tipo = 'VENTA'
  AND (s.code IS NULL OR s.code <> 'deleted')
  AND (v.total - v.pagado) <> 0
ORDER BY v.id, mc.fecha;

-- 3) Resumen: cuánto cambiaría el total de "deuda por movimientos" de Juan
--    Taller si aplicamos la corrección (para comparar contra Deuda legacy)
SELECT
    SUM(-(v.total - v.pagado)) AS suma_esperada_post_normalizacion_ventas_abiertas
FROM ventas v
LEFT JOIN status s ON s.id = v.estado_id
WHERE v.cliente_id = 1
  AND (s.code IS NULL OR s.code <> 'deleted')
  AND (v.total - v.pagado) <> 0;
