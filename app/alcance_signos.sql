-- ============================================================================
-- Mide el alcance del problema de signos en TODA la base (no solo cliente 1).
-- Para cada venta abierta (no pagada del todo, no eliminada), compara:
--   a) lo que dice la tabla `ventas` (total - pagado = lo que realmente debe)
--   b) la suma de sus propios movimientos tipo VENTA en movimientos_cliente
-- Bajo la convención nueva (VENTA negativo = deuda), (b) debería ser
-- exactamente -(a). Si (b) da positivo, o no coincide con -(a), esa venta
-- quedó con el signo viejo (heredado) y hay que corregirla a mano.
-- ============================================================================

SELECT
    v.id AS venta_id,
    v.cliente_id,
    v.total,
    v.pagado,
    (v.total - v.pagado) AS saldo_pendiente_real,
    COALESCE(m.suma_movimientos_venta, 0) AS suma_movimientos_venta,
    -- lo esperado bajo la convención nueva:
    -(v.total - v.pagado) AS esperado_bajo_convencion_nueva,
    COALESCE(m.suma_movimientos_venta, 0) - (-(v.total - v.pagado)) AS diferencia
FROM ventas v
LEFT JOIN (
    SELECT venta_id, SUM(monto) AS suma_movimientos_venta
    FROM movimientos_cliente
    WHERE tipo = 'VENTA'
    GROUP BY venta_id
) m ON m.venta_id = v.id
LEFT JOIN status s ON s.id = v.estado_id
WHERE (s.code IS NULL OR s.code <> 'deleted')
  AND (v.total - v.pagado) <> 0        -- solo ventas con saldo pendiente real
ORDER BY ABS(COALESCE(m.suma_movimientos_venta, 0) - (-(v.total - v.pagado))) DESC
LIMIT 200;

-- Resumen: cuántas ventas abiertas tienen el signo mal vs bien
SELECT
    CASE
        WHEN COALESCE(m.suma_movimientos_venta, 0) = -(v.total - v.pagado) THEN 'OK (signo correcto)'
        WHEN m.suma_movimientos_venta IS NULL THEN 'SIN movimiento (huerfana)'
        ELSE 'MAL (signo/valor no coincide)'
    END AS estado,
    COUNT(*) AS cantidad,
    SUM(v.total - v.pagado) AS saldo_pendiente_total
FROM ventas v
LEFT JOIN (
    SELECT venta_id, SUM(monto) AS suma_movimientos_venta
    FROM movimientos_cliente
    WHERE tipo = 'VENTA'
    GROUP BY venta_id
) m ON m.venta_id = v.id
LEFT JOIN status s ON s.id = v.estado_id
WHERE (s.code IS NULL OR s.code <> 'deleted')
  AND (v.total - v.pagado) <> 0
GROUP BY 1
ORDER BY cantidad DESC;
