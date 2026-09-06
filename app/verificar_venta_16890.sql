-- Verifica el signo real de venta.total para la venta que generó el
-- movimiento 1531 (monto +42.800,00, "Actualizado de 42800 a 42800").
-- Si total sale NEGATIVO acá, confirma que actualizar_venta() está invirtiendo
-- el signo de forma inconsistente con el resto del sistema.
SELECT id, cliente_id, total, pagado, saldo, fecha_venta, estado_id
FROM ventas
WHERE id = 16890;

-- De paso, chequeamos si hay ventas con total negativo para el cliente 1
-- (no deberia haber ninguna en un sistema normal de ventas)
SELECT id, total, pagado, saldo, fecha_venta
FROM ventas
WHERE cliente_id = 1 AND total < 0
ORDER BY fecha_venta;
