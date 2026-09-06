-- ============================================================================
-- AJUSTE FINAL — piloto cliente 1 (Juan Taller)
--
-- En vez de perseguir cada movimiento "huérfano" de ventas que ya están
-- pagadas (ruido histórico que no afecta a nadie hoy), este script agrega
-- UN solo movimiento AJUSTE nuevo que compensa exactamente la diferencia
-- entre "Deuda (movimientos)" y "Deuda (legacy)" tal como están HOY.
--
-- De acá en adelante, mientras no se editen más datos viejos a mano, cada
-- venta/pago nuevo ya se registra bien (confirmado: crear_venta,
-- actualizar_venta y registrar_pago_cliente usan el signo correcto), así que
-- el total debería seguir cuadrando solo sin necesitar otro ajuste como este.
--
-- Por qué INSERT y no UPDATE del ajuste viejo (id 1848):
-- Esa fila ya tiene un historial raro (en algún momento pasó de -268.060 a
-- -303.660 sin que la app la haya tocado — crear_ajuste() solo hace INSERT,
-- nunca UPDATE). Para no seguir editando una fila ya sospechosa y dejar
-- rastro claro de qué se hizo y cuándo, este script inserta un AJUSTE nuevo
-- en vez de modificar el 1848. El resultado final es el mismo.
--
-- IMPORTANTE sobre el cliente SQL: si tu herramienta tiene "autocommit"
-- activado, el BEGIN/COMMIT de este script no agrupa nada. Fijate si tenés
-- un modo "manual transaction" / "autocommit: off", o usá psql.
-- ============================================================================

BEGIN;

-- 0) ANTES: estado actual
SELECT
    (SELECT SUM(monto) FROM movimientos_cliente WHERE cliente_id = 1) AS suma_movimientos_antes,
    (SELECT SUM(v.total - v.pagado)
       FROM ventas v LEFT JOIN status s ON s.id = v.estado_id
       WHERE v.cliente_id = 1 AND (s.code IS NULL OR s.code <> 'deleted')) AS deuda_legacy,
    (SELECT SUM(monto) FROM movimientos_cliente WHERE cliente_id = 1)
      + (SELECT SUM(v.total - v.pagado)
           FROM ventas v LEFT JOIN status s ON s.id = v.estado_id
           WHERE v.cliente_id = 1 AND (s.code IS NULL OR s.code <> 'deleted')) AS diferencia_actual;

-- 1) Inserta el ajuste que compensa exactamente esa diferencia.
--    Si ya estuviera en 0 (por ejemplo si corrés esto dos veces), no inserta nada.
WITH calc AS (
    SELECT
        (SELECT SUM(monto) FROM movimientos_cliente WHERE cliente_id = 1) AS suma_movimientos,
        (SELECT SUM(v.total - v.pagado)
           FROM ventas v LEFT JOIN status s ON s.id = v.estado_id
           WHERE v.cliente_id = 1 AND (s.code IS NULL OR s.code <> 'deleted')) AS deuda_legacy
)
INSERT INTO movimientos_cliente (cliente_id, tipo, monto, fecha, observaciones)
SELECT
    1,
    'AJUSTE',
    -1 * (suma_movimientos + deuda_legacy),
    NOW(),
    'Ajuste manual de normalización histórica (2026-09): compensa ruido de ' ||
    'movimientos de ventas ya saldadas, para alinear Deuda(movimientos) con ' ||
    'Deuda(legacy). No modifica ventas ni pagos existentes. Diferencia compensada: ' ||
    (suma_movimientos + deuda_legacy)::text
FROM calc
WHERE (suma_movimientos + deuda_legacy) <> 0;

-- 2) DESPUÉS: esto debería dar 0 en diferencia_deberia_ser_0
SELECT
    (SELECT SUM(monto) FROM movimientos_cliente WHERE cliente_id = 1) AS suma_movimientos_despues,
    (SELECT SUM(v.total - v.pagado)
       FROM ventas v LEFT JOIN status s ON s.id = v.estado_id
       WHERE v.cliente_id = 1 AND (s.code IS NULL OR s.code <> 'deleted')) AS deuda_legacy,
    (SELECT SUM(monto) FROM movimientos_cliente WHERE cliente_id = 1)
      + (SELECT SUM(v.total - v.pagado)
           FROM ventas v LEFT JOIN status s ON s.id = v.estado_id
           WHERE v.cliente_id = 1 AND (s.code IS NULL OR s.code <> 'deleted')) AS diferencia_deberia_ser_0;

-- ============================================================================
-- PARÁ ACÁ. No corras las líneas de abajo todavía.
--
-- Corré todo el archivo HASTA ACÁ (desde el BEGIN hasta la consulta de
-- verificación de arriba), mirá "diferencia_deberia_ser_0", y recién ahí
-- ejecutá UNA de las dos líneas siguientes, a mano, por separado:
--
--   COMMIT;    -- si diferencia_deberia_ser_0 dio 0
--   ROLLBACK;  -- si dio distinto de 0 (no se guarda nada, quedamos como antes)
--
-- Nota: esto NO toca la venta 16890 (todavía pendiente de restaurar). Es
-- independiente — la podés restaurar antes o después de correr esto, en
-- cualquier orden, sin que se rompa nada.
-- ============================================================================
