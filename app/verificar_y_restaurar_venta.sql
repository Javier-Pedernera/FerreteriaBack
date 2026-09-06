-- ============================================================================
-- PASO 1: verificar qué pasó realmente con la venta 16890
-- ============================================================================

-- ¿La venta todavía existe como fila en la tabla `ventas`?
SELECT v.id, v.cliente_id, v.total, v.pagado, v.saldo, v.fecha_venta,
       s.code AS estado_code, s.label AS estado_label
FROM ventas v
LEFT JOIN status s ON s.id = v.estado_id
WHERE v.id = 16890;

-- Si la fila de arriba SÍ aparece (aunque diga estado "Eliminado"/deleted),
-- fue un borrado LÓGICO (soft delete) hecho desde el botón "eliminar" de la
-- app -- eso es fácil de revertir, ver PASO 2 más abajo.
--
-- Si la consulta de arriba NO devuelve NINGUNA fila, la venta se borró con un
-- DELETE físico (por SQL directo). Ahí la recuperación es distinta y más
-- delicada -- avisame antes de tocar nada más si es este el caso.

-- ============================================================================
-- PASO 2: si fue borrado lógico (la fila existe con estado "deleted"),
-- esto la reactiva. NO la corras si el PASO 1 no devolvió ninguna fila.
-- ============================================================================

BEGIN;

UPDATE ventas
SET estado_id = (SELECT id FROM status WHERE code = 'on_account')
WHERE id = 16890;

-- Verificación
SELECT v.id, v.total, v.pagado, v.saldo, s.code AS estado_code
FROM ventas v
LEFT JOIN status s ON s.id = v.estado_id
WHERE v.id = 16890;

-- Si el estado_code ahora dice "on_account" y total/pagado/saldo están bien:
COMMIT;
-- Si no:
-- ROLLBACK;
