-- Ventas de Juan Taller YA PAGADAS (total = pagado) que sin embargo tienen
-- movimientos VENTA cuya suma no da 0 — son las que están ensuciando el
-- total general aunque no tengan saldo pendiente.
SELECT
    v.id AS venta_id,
    v.total,
    v.pagado,
    (v.total - v.pagado) AS saldo_pendiente_real,  -- debería ser 0
    m.suma_actual AS suma_movimientos_venta,        -- debería ser 0 también
    m.cantidad
FROM ventas v
JOIN (
    SELECT venta_id, SUM(monto) AS suma_actual, COUNT(*) AS cantidad
    FROM movimientos_cliente
    WHERE tipo = 'VENTA'
    GROUP BY venta_id
) m ON m.venta_id = v.id
LEFT JOIN status s ON s.id = v.estado_id
WHERE v.cliente_id = 1
  AND (s.code IS NULL OR s.code <> 'deleted')
  AND (v.total - v.pagado) = 0        -- YA PAGADA, no debería nada
  AND m.suma_actual <> 0              -- pero su movimiento no da 0
ORDER BY ABS(m.suma_actual) DESC;

-- Suma total de este "ruido" (ventas cerradas con movimiento distinto de 0)
SELECT SUM(m.suma_actual) AS ruido_total
FROM ventas v
JOIN (
    SELECT venta_id, SUM(monto) AS suma_actual
    FROM movimientos_cliente
    WHERE tipo = 'VENTA'
    GROUP BY venta_id
) m ON m.venta_id = v.id
LEFT JOIN status s ON s.id = v.estado_id
WHERE v.cliente_id = 1
  AND (s.code IS NULL OR s.code <> 'deleted')
  AND (v.total - v.pagado) = 0
  AND m.suma_actual <> 0;
