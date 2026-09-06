-- ============================================================================
-- CORRECCIÓN REAL — piloto cliente 1 (Juan Taller)
-- Versión simplificada: para las ventas "MAL" donde el monto ya es correcto
-- pero con el signo dado vuelta, simplemente se invierte el signo de cada
-- movimiento (UPDATE monto = -monto) — no se borra ni se pierde historial.
-- Para las "HUERFANA" (sin ningún movimiento), se inserta uno nuevo, porque
-- ahí no hay nada que invertir.
--
-- Requisitos antes de correr esto:
--   1) Backup hecho (1_backup.sh)
--   2) Ya revisaste el preview (2_preview_normalizacion_cliente1.sql)
--   3) La venta 16890 tiene que estar con estado activo (no "deleted") para
--      que este script la incluya. Si todavía está en estado "deleted",
--      corré primero el PASO 2 de verificar_y_restaurar_venta.sql.
--
-- Corre todo dentro de una transacción — revisá el "DESPUÉS" antes de
-- decidir COMMIT o ROLLBACK.
--
-- IMPORTANTE sobre el cliente SQL: si tu herramienta tiene "autocommit"
-- activado, cada sentencia se confirma sola apenas la ejecutás, y el BEGIN/
-- COMMIT de este script no van a agrupar nada (fue justo lo que rompió la
-- versión anterior con la tabla temporal). Antes de correr esto, fijate si
-- tu cliente tiene un modo "manual transaction" / "autocommit: off" y
-- activalo, o usá psql (ahí el BEGIN sí abre una transacción manual real).
-- ============================================================================

BEGIN;

-- 0) Snapshot ANTES: deuda total de Juan Taller según movimientos (todo tipo)
SELECT SUM(monto) AS deuda_movimientos_antes
FROM movimientos_cliente
WHERE cliente_id = 1;

-- 1) Cuántas ventas va a tocar este script (chequealo contra el preview)
SELECT COUNT(*) AS cantidad_ventas_a_corregir
FROM ventas v
LEFT JOIN status s ON s.id = v.estado_id
LEFT JOIN (
    SELECT venta_id, SUM(monto) AS suma_actual
    FROM movimientos_cliente
    WHERE tipo = 'VENTA'
    GROUP BY venta_id
) m ON m.venta_id = v.id
WHERE v.cliente_id = 1
  AND (s.code IS NULL OR s.code <> 'deleted')
  AND (v.total - v.pagado) <> 0
  AND COALESCE(m.suma_actual, 0) <> -(v.total - v.pagado);

-- 2) Ventas "MAL" pero de patrón simple (el monto ya es el correcto, solo
--    con el signo dado vuelta): se invierte el signo de CADA movimiento que
--    tengan (uno o varios — invertir cada término da el mismo resultado que
--    invertir la suma). No se borra nada, no se pierde historial.
UPDATE movimientos_cliente mc
SET monto = -monto
WHERE mc.tipo = 'VENTA'
  AND mc.venta_id IN (
    SELECT v.id
    FROM ventas v
    LEFT JOIN status s ON s.id = v.estado_id
    JOIN (
        SELECT venta_id, SUM(monto) AS suma_actual
        FROM movimientos_cliente
        WHERE tipo = 'VENTA'
        GROUP BY venta_id
    ) m ON m.venta_id = v.id
    WHERE v.cliente_id = 1
      AND (s.code IS NULL OR s.code <> 'deleted')
      AND (v.total - v.pagado) <> 0
      AND m.suma_actual = (v.total - v.pagado)   -- exactamente el positivo del valor correcto
  );

-- 3) Ventas "HUERFANA" (sin ningún movimiento VENTA): ahí no hay nada que
--    invertir, así que se inserta uno nuevo con el monto correcto.
INSERT INTO movimientos_cliente (cliente_id, tipo, monto, venta_id, fecha, observaciones)
SELECT
    1,
    'VENTA',
    -(v.total - v.pagado),
    v.id,
    v.fecha_venta,
    'Normalización: venta sin movimiento previo, se crea uno con el saldo ' ||
    'pendiente real (total - pagado) en negativo.'
FROM ventas v
LEFT JOIN status s ON s.id = v.estado_id
LEFT JOIN movimientos_cliente mc ON mc.venta_id = v.id AND mc.tipo = 'VENTA'
WHERE v.cliente_id = 1
  AND (s.code IS NULL OR s.code <> 'deleted')
  AND (v.total - v.pagado) <> 0
  AND mc.id IS NULL;

-- 4) Red de seguridad: ventas que siguen sin cerrar después de los dos pasos
--    de arriba (ni encajaban en el "sign flip" simple, ni eran huérfanas) —
--    si esto devuelve filas, NO son casos simples, no las toques a ciegas,
--    avisame y las vemos una por una.
SELECT
    v.id AS venta_id,
    v.total,
    v.pagado,
    (v.total - v.pagado) AS saldo_pendiente_real,
    SUM(mc.monto) AS suma_movimientos_actual
FROM ventas v
LEFT JOIN status s ON s.id = v.estado_id
JOIN movimientos_cliente mc ON mc.venta_id = v.id AND mc.tipo = 'VENTA'
WHERE v.cliente_id = 1
  AND (s.code IS NULL OR s.code <> 'deleted')
  AND (v.total - v.pagado) <> 0
GROUP BY v.id, v.total, v.pagado
HAVING SUM(mc.monto) <> -(v.total - v.pagado);

-- 5) Snapshot DESPUÉS
SELECT SUM(monto) AS deuda_movimientos_despues
FROM movimientos_cliente
WHERE cliente_id = 1;

-- 6) Verificación: debería dar 0 diferencia contra "Deuda (legacy)"
SELECT
    (SELECT SUM(monto) FROM movimientos_cliente WHERE cliente_id = 1) AS suma_movimientos,
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
-- verificación de arriba), mirá el resultado de "diferencia_deberia_ser_0",
-- y recién ahí ejecutá UNA de las dos líneas siguientes, a mano, por separado:
--
--   COMMIT;    -- si diferencia_deberia_ser_0 dio 0
--   ROLLBACK;  -- si dio distinto de 0 (no se guarda nada, quedamos como antes)
--
-- Si tu cliente SQL no te deja pausar a mitad de un script (algunos corren
-- todo el archivo de un tirón), ejecutalo statement por statement en vez de
-- "correr todo", para poder frenar antes del COMMIT/ROLLBACK.
-- ============================================================================
