-- ============================================================================
-- Restaura el movimiento borrado por error para la venta 16890 (cliente 1,
-- Juan Taller). Se había eliminado el movimiento tipo VENTA de +42800.00 que
-- reflejaba el cargo real de esa venta. Lo reinsertamos con el signo
-- ORIGINAL (positivo = cargo/deuda), no negativo.
-- ============================================================================

BEGIN;

-- 0) Verificación previa: confirmar que la venta 16890 sigue intacta en
--    `ventas` (total 42800) y que en movimientos_cliente NO hay nada para
--    ella (para no duplicar si por algo ya se restauró)
SELECT id, cliente_id, total, pagado, saldo
FROM ventas
WHERE id = 16890;

SELECT * FROM movimientos_cliente
WHERE venta_id = 16890;

-- Si la segunda consulta NO devuelve filas, seguí con el INSERT.
-- Si YA devuelve una fila, NO insertes de nuevo (haría doble conteo) —
-- avisame y lo resolvemos distinto.

-- 1) Reinsertar el movimiento con el signo correcto (positivo = cargo)
INSERT INTO movimientos_cliente (cliente_id, tipo, monto, venta_id, fecha, observaciones)
VALUES (
    1,
    'VENTA',
    42800.00,
    16890,
    '2026-08-04 20:14:30.693',  -- misma fecha que tenía el movimiento original (id 1531)
    'Restaurado tras eliminación accidental del movimiento original (id 1531). ' ||
    'Se reinserta con signo positivo (cargo real de la venta #16890), no negativo.'
);

-- 2) Verificación posterior
SELECT * FROM movimientos_cliente
WHERE venta_id = 16890
ORDER BY fecha;

-- Si todo se ve bien:
COMMIT;
-- Si algo no cierra:
-- ROLLBACK;
