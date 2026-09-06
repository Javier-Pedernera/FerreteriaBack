-- ============================================================================
-- Diagnostico saldo_favor - Ferreteria
-- Compara el valor cacheado en clientes.saldo_favor contra lo que el propio
-- codigo del backend considera "credito real" (VentaService.obtener_credito_disponible
-- en ventas_service.py: SUM(monto) de movimientos tipo CREDITO menos SUM(monto)
-- de movimientos tipo USO_CREDITO).
--
-- Ojo con el nombre de tabla/enum: SQLAlchemy con db.Enum(TipoMovimientoCliente)
-- guarda por defecto el NOMBRE del enum en mayusculas (VENTA, PAGO, AJUSTE,
-- CREDITO, USO_CREDITO), no el .value en minuscula. Si en tu base los valores
-- estan en minuscula, cambia 'CREDITO'/'USO_CREDITO'/etc. por 'credito'/'uso_credito'.
-- ============================================================================

-- 1) Un cliente puntual: reemplaza el 1 por el cliente_id que estas investigando
\set cliente_id 1

-- 1a) Valor cacheado actual (el que devuelve la API)
SELECT id, nombre, saldo_favor AS saldo_favor_cacheado
FROM clientes
WHERE id = :cliente_id;

-- 1b) Breakdown por tipo de movimiento (para ver con que numeros esta jugando)
SELECT
    tipo,
    COUNT(*)        AS cantidad,
    SUM(monto)      AS suma_monto,
    MIN(fecha)      AS primera_fecha,
    MAX(fecha)      AS ultima_fecha
FROM movimientos_cliente
WHERE cliente_id = :cliente_id
GROUP BY tipo
ORDER BY tipo;

-- 1c) "Credito real" segun la logica que usa el backend para aplicar pagos
--     (ventas_service.py -> obtener_credito_disponible): CREDITO - USO_CREDITO
SELECT
    COALESCE(SUM(monto) FILTER (WHERE tipo = 'CREDITO'), 0)      AS total_creditos,
    COALESCE(SUM(monto) FILTER (WHERE tipo = 'USO_CREDITO'), 0)  AS total_uso_credito,
    COALESCE(SUM(monto) FILTER (WHERE tipo = 'CREDITO'), 0)
      + COALESCE(SUM(monto) FILTER (WHERE tipo = 'USO_CREDITO'), 0) AS credito_real_segun_ledger
FROM movimientos_cliente
WHERE cliente_id = :cliente_id;

-- 1d) Comparacion directa: cache vs ledger, y la diferencia (esto es lo que
--     buscamos: si no da 0, el cache esta desincronizado del historial real)
SELECT
    c.id,
    c.nombre,
    c.saldo_favor AS saldo_favor_cacheado,
    COALESCE((
        SELECT SUM(monto) FILTER (WHERE tipo = 'CREDITO')
             + SUM(monto) FILTER (WHERE tipo = 'USO_CREDITO')
        FROM movimientos_cliente m
        WHERE m.cliente_id = c.id
    ), 0) AS credito_real_segun_ledger,
    c.saldo_favor - COALESCE((
        SELECT SUM(monto) FILTER (WHERE tipo = 'CREDITO')
             + SUM(monto) FILTER (WHERE tipo = 'USO_CREDITO')
        FROM movimientos_cliente m
        WHERE m.cliente_id = c.id
    ), 0) AS diferencia
FROM clientes c
WHERE c.id = :cliente_id;

-- 1e) Todos los movimientos del cliente, en orden cronologico, con saldo
--     acumulado de deuda replicando la logica de recalcular_saldos()
--     (cliente_finanzas_service.py) para que veas exactamente como se arma
--     el numero paso a paso. OJO: esta logica tiene el bug de doble conteo
--     en cuentas viejas (aplicaciones de pago registradas como VENTA en vez
--     de PAGO), asi que el resultado de esta columna puede NO coincidir con
--     el cache ni con el "credito real" de 1c/1d -- es solo para ver el detalle.
SELECT
    id,
    tipo,
    monto,
    venta_id,
    pago_id,
    fecha,
    observaciones,
    SUM(
        CASE
            WHEN tipo IN ('VENTA', 'AJUSTE') THEN monto
            WHEN tipo = 'PAGO' THEN -monto
            ELSE 0
        END
    ) OVER (ORDER BY fecha, id) AS deuda_acumulada_replicando_recalcular_saldos
FROM movimientos_cliente
WHERE cliente_id = :cliente_id
ORDER BY fecha, id;


-- ============================================================================
-- 2) TODOS los clientes: para ver cuantos mas tienen el cache desincronizado
--    y de que magnitud es cada caso. Muy util para saber si esto es un caso
--    aislado o un problema generalizado.
-- ============================================================================
SELECT
    c.id,
    c.nombre,
    c.saldo_favor AS saldo_favor_cacheado,
    COALESCE(led.credito_real, 0) AS credito_real_segun_ledger,
    c.saldo_favor - COALESCE(led.credito_real, 0) AS diferencia
FROM clientes c
LEFT JOIN (
    SELECT
        cliente_id,
        SUM(monto) FILTER (WHERE tipo = 'CREDITO')
          + SUM(monto) FILTER (WHERE tipo = 'USO_CREDITO') AS credito_real
    FROM movimientos_cliente
    GROUP BY cliente_id
) led ON led.cliente_id = c.id
WHERE c.saldo_favor <> 0
   OR COALESCE(led.credito_real, 0) <> 0
ORDER BY ABS(c.saldo_favor - COALESCE(led.credito_real, 0)) DESC;
