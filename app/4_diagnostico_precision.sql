-- Ver los valores exactos, sin redondear, para las 7 ventas en cuestión
SELECT
    v.id AS venta_id,
    v.total,
    v.pagado,
    (v.total - v.pagado) AS saldo_pendiente,
    m.suma_actual,
    (v.total - v.pagado) - m.suma_actual AS diferencia_exacta
FROM ventas v
JOIN (
    SELECT venta_id, SUM(monto) AS suma_actual
    FROM movimientos_cliente
    WHERE tipo = 'VENTA'
    GROUP BY venta_id
) m ON m.venta_id = v.id
WHERE v.id IN (14983, 15240, 15802, 16233, 16940, 17240, 17383);
