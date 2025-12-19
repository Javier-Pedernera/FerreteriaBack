from sqlalchemy import func
from datetime import date, timedelta
from app import db
from app.models.venta import Venta
from app.models.cliente import Cliente
from app.models.detalle_venta import DetalleVenta
from app.models.producto import Producto
from app.models.pedido_proveedor import PedidoProveedor
from app.models.detalle_pedido_proveedor import DetallePedidoProveedor


class EstadisticasService:

    # --------------------------------------------------
    # VENTAS POR PERÍODO (SOLO COBRADAS)
    # --------------------------------------------------
    @staticmethod
    def ventas_por_periodo(periodo='diario'):

        if periodo == 'diario':
            q = db.session.query(
                func.date(Venta.fecha_venta).label('fecha'),
                func.sum(Venta.total).label('totalVentas'),
                func.count(Venta.id).label('cantidadVentas')
            ).filter(
                Venta.fecha_pago.isnot(None)
            ).group_by(
                func.date(Venta.fecha_venta)
            ).order_by(
                func.date(Venta.fecha_venta)
            )

        elif periodo == 'mensual':
            q = db.session.query(
                func.concat(
                    func.extract('year', Venta.fecha_venta).cast(db.String),
                    '-',
                    func.lpad(func.extract('month', Venta.fecha_venta).cast(db.String), 2, '0')
                ).label('fecha'),
                func.sum(Venta.total).label('totalVentas'),
                func.count(Venta.id).label('cantidadVentas')
            ).filter(
                Venta.fecha_pago.isnot(None)
            ).group_by('fecha').order_by('fecha')

        elif periodo == 'anual':
            q = db.session.query(
                func.extract('year', Venta.fecha_venta).cast(db.String).label('fecha'),
                func.sum(Venta.total).label('totalVentas'),
                func.count(Venta.id).label('cantidadVentas')
            ).filter(
                Venta.fecha_pago.isnot(None)
            ).group_by('fecha').order_by('fecha')
        else:
            return []

        return [
            {
                'fecha': str(r.fecha),
                'totalVentas': float(r.totalVentas),
                'cantidadVentas': r.cantidadVentas
            }
            for r in q.all()
        ]

    # --------------------------------------------------
    # TOP CLIENTES (SOLO COBRADAS)
    # --------------------------------------------------
    @staticmethod
    def top_clientes(limite=10):
        q = db.session.query(
            Cliente.nombre.label('cliente'),
            func.sum(Venta.total).label('totalCompras')
        ).join(
            Venta, Venta.cliente_id == Cliente.id
        ).filter(
            Venta.fecha_pago.isnot(None)
        ).group_by(
            Cliente.id
        ).order_by(
            func.sum(Venta.total).desc()
        ).limit(limite)

        return [
            {
                'cliente': r.cliente,
                'totalCompras': float(r.totalCompras)
            }
            for r in q.all()
        ]

    # --------------------------------------------------
    # VENTAS POR CLIENTE
    # --------------------------------------------------
    @staticmethod
    def ventas_cliente(cliente_id, periodo='diario'):

        if periodo == 'diario':
            q = db.session.query(
                func.date(Venta.fecha_pago).label('fecha'),
                func.sum(Venta.total).label('totalVentas'),
                func.count(Venta.id).label('cantidadVentas')
            ).filter(
                Venta.cliente_id == cliente_id,
                Venta.fecha_pago.isnot(None)
            ).group_by(
                func.date(Venta.fecha_pago)
            ).order_by(
                func.date(Venta.fecha_pago)
            )

        elif periodo == 'mensual':
            q = db.session.query(
                func.concat(
                    func.extract('year', Venta.fecha_pago).cast(db.String),
                    '-',
                    func.lpad(func.extract('month', Venta.fecha_pago).cast(db.String), 2, '0')
                ).label('fecha'),
                func.sum(Venta.total).label('totalVentas'),
                func.count(Venta.id).label('cantidadVentas')
            ).filter(
                Venta.cliente_id == cliente_id,
                Venta.fecha_pago.isnot(None)
            ).group_by('fecha').order_by('fecha')

        elif periodo == 'anual':
            q = db.session.query(
                func.extract('year', Venta.fecha_pago).cast(db.String).label('fecha'),
                func.sum(Venta.total).label('totalVentas'),
                func.count(Venta.id).label('cantidadVentas')
            ).filter(
                Venta.cliente_id == cliente_id,
                Venta.fecha_pago.isnot(None)
            ).group_by('fecha').order_by('fecha')
        else:
            return []

        return [
            {
                'fecha': str(r.fecha),
                'totalVentas': float(r.totalVentas),
                'cantidadVentas': r.cantidadVentas
            }
            for r in q.all()
        ]

    # --------------------------------------------------
    # RESUMEN GENERAL
    # --------------------------------------------------
    @staticmethod
    def resumen():
        hoy = date.today()
        mes = hoy.month
        anio = hoy.year

        # Ventas hoy
        total_hoy, cant_hoy = db.session.query(
            func.coalesce(func.sum(Venta.total), 0),
            func.count(Venta.id)
        ).filter(
            Venta.fecha_pago.isnot(None),
            func.date(Venta.fecha_venta) == hoy
        ).first()

        # Ventas mes
        total_mes, cant_mes = db.session.query(
            func.coalesce(func.sum(Venta.total), 0),
            func.count(Venta.id)
        ).filter(
            Venta.fecha_pago.isnot(None),
            func.extract('month', Venta.fecha_venta) == mes,
            func.extract('year', Venta.fecha_venta) == anio
        ).first()

        # Top productos
        top_productos = db.session.query(
            Producto.nombre,
            func.sum(DetalleVenta.cantidad),
            func.sum(DetalleVenta.cantidad * DetalleVenta.precio_unitario)
        ).join(
            Producto, Producto.id == DetalleVenta.producto_id
        ).join(
            Venta, Venta.id == DetalleVenta.venta_id
        ).filter(
            Venta.fecha_pago.isnot(None),
            func.extract('month', Venta.fecha_venta) == mes,
            func.extract('year', Venta.fecha_venta) == anio
        ).group_by(
            Producto.nombre
        ).order_by(
            func.sum(DetalleVenta.cantidad * DetalleVenta.precio_unitario).desc()
        ).limit(5).all()

        # Ventas últimos 15 días
        inicio = hoy - timedelta(days=15)
        ventas_por_dia = db.session.query(
            func.date(Venta.fecha_venta),
            func.sum(Venta.total),
            func.count(Venta.id)
        ).filter(
            Venta.fecha_pago.isnot(None),
            Venta.fecha_pago >= inicio
        ).group_by(
            func.date(Venta.fecha_venta)
        ).order_by(
            func.date(Venta.fecha_venta)
        ).all()

        return {
            "ventas_hoy": {
                "total": float(total_hoy),
                "cantidad": cant_hoy
            },
            "ventas_mes": {
                "total": float(total_mes),
                "cantidad": cant_mes
            },
            "top_productos": [
                {"producto": p[0], "cantidad": int(p[1]), "total": float(p[2])}
                for p in top_productos
            ],
            "ventas_por_dia": [
                {"fecha": str(v[0]), "totalVentas": float(v[1]), "cantidadVentas": int(v[2])}
                for v in ventas_por_dia
            ]
        }

    # --------------------------------------------------
    # INGRESOS / EGRESOS DIARIOS
    # --------------------------------------------------
    @staticmethod
    def resumen_ingresos_egresos_diarios(fecha=None):
        if fecha is None:
            fecha = date.today()

        ingresos = db.session.query(
            func.coalesce(func.sum(Venta.total), 0),
            func.count(Venta.id)
        ).filter(
            Venta.fecha_pago.isnot(None),
            func.date(Venta.fecha_venta) == fecha
        ).one()

        total_por_pedido = (
            db.session.query(
                DetallePedidoProveedor.pedido_id,
                func.sum(
                    DetallePedidoProveedor.cantidad * DetallePedidoProveedor.precio_unitario
                ).label('subtotal')
            ).group_by(
                DetallePedidoProveedor.pedido_id
            ).subquery()
        )

        egresos = db.session.query(
            func.coalesce(func.sum(total_por_pedido.c.subtotal), 0),
            func.count(PedidoProveedor.id)
        ).join(
            total_por_pedido,
            PedidoProveedor.id == total_por_pedido.c.pedido_id
        ).filter(
            func.date(PedidoProveedor.fecha_pedido) == fecha
        ).one()

        return {
            "fecha": fecha.isoformat(),
            "ingresos": {
                "total": float(ingresos[0]),
                "cantidad": ingresos[1]
            },
            "egresos": {
                "total": float(egresos[0]),
                "cantidad": egresos[1]
            }
        }

    # --------------------------------------------------
    # GANANCIA MENSUAL (REAL)
    # --------------------------------------------------
    @staticmethod
    def ganancia_mensual():
        resultados = (
            db.session.query(
                func.extract('year', Venta.fecha_venta).label('anio'),
                func.extract('month', Venta.fecha_venta).label('mes'),
                func.sum(
                    DetalleVenta.cantidad * DetalleVenta.precio_unitario
                ).label('total_ventas'),
                func.sum(
                    DetalleVenta.cantidad *
                    (DetalleVenta.precio_unitario - DetalleVenta.precio_costo)
                ).label('ganancia_neta')
            )
            .join(DetalleVenta, DetalleVenta.venta_id == Venta.id)
            .filter(Venta.fecha_pago.isnot(None))
            .group_by('anio', 'mes')
            .order_by('anio', 'mes')
            .all()
        )

        return [
            {
                "mes": f"{int(r.anio)}-{int(r.mes):02d}",
                "totalVentas": float(r.total_ventas),
                "gananciaNeta": float(r.ganancia_neta),
                "porcentajeGanancia": (
                    round((r.ganancia_neta / r.total_ventas) * 100, 2)
                    if r.total_ventas and r.total_ventas > 0
                    else 0
                )
            }
            for r in resultados
        ]