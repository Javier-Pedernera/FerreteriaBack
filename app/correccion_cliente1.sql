-- ============================================================================
-- Corrección: saldo_favor de Juan Taller (cliente 1)
-- El cache (clientes.saldo_favor = 42800.00) no está respaldado por ningún
-- movimiento tipo CREDITO en movimientos_cliente (credito_real_segun_ledger = 0).
-- Se corrige el cache a 0 y se deja un movimiento de auditoría explicando el
-- porqué, para no perder el rastro de que hubo una corrección manual.
--
-- Revisá los valores antes de correrlo. Se ejecuta dentro de una transacción:
-- si algo no cierra, hacé ROLLBACK en vez de COMMIT.
-- ============================================================================

BEGIN;

-- 1) Snapshot de cómo está ANTES de tocar nada (para tener el "antes" a mano)
SELECT id, nombre, saldo_favor AS saldo_favor_antes
FROM clientes
WHERE id = 1;

-- 2) Movimiento de auditoría: deja constancia de la corrección en el historial
--    (tipo AJUSTE, monto 0 porque no está moviendo deuda real, solo corrige el cache)
INSERT INTO movimientos_cliente (cliente_id, tipo, monto, fecha, observaciones)
VALUES (
    1,
    'AJUSTE',
    0.00,
    NOW(),
    'Corrección manual: saldo_favor cacheado en clientes (42800.00) no estaba respaldado ' ||
    'por ningún movimiento tipo CREDITO en el ledger (credito_real_segun_ledger = 0.00). ' ||
    'Se corrige clientes.saldo_favor de 42800.00 a 0.00. Ver conversación de diagnóstico 2026-09-01.'
);

-- 3) Corrección del cache
UPDATE clientes
SET saldo_favor = 0.00
WHERE id = 1;

-- 4) Verificación DESPUÉS del cambio
SELECT id, nombre, saldo_favor AS saldo_favor_despues
FROM clientes
WHERE id = 1;

-- Si todo se ve bien:
COMMIT;
-- Si algo no cierra:
-- ROLLBACK;
