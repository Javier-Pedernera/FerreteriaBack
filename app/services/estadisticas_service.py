from sqlalchemy import func, extract
from app import db
from app.models.detalle_pedido_proveedor import DetallePedidoProveedor
from app.models.pedido_proveedor import PedidoProveedor
from app.models.venta import Venta
from app.models.cliente import Cliente
from datetime import datetime, date, timedelta
from app import db
from app.models.detalle_venta import DetalleVenta
from app.models.producto import Producto

class EstadisticasService:

    @staticmethod
    def ventas_por_periodo(periodo='diario'):
        """
        Retorna lista con dicts {fecha: str, totalVentas: float, cantidadVentas: int}
        agrupado por día, mes o año según 'periodo'
        """
        q = db.session.query(
            Venta.fecha_venta,
            func.sum(Venta.total).label('totalVentas'),
            func.count(Venta.id).label('cantidadVentas')
        )

        if periodo == 'diario':
            q = db.session.query(
                func.date(Venta.fecha_venta).label('fecha'),
                func.sum(Venta.total).label('totalVentas'),
                func.count(Venta.id).label('cantidadVentas')
            ).group_by(func.date(Venta.fecha_venta)).order_by(func.date(Venta.fecha_venta))
        elif periodo == 'mensual':
            q = db.session.query(
                func.concat(
                    func.extract('year', Venta.fecha_venta).cast(db.String),
                    '-',
                    func.lpad(func.extract('month', Venta.fecha_venta).cast(db.String), 2, '0')
                ).label('fecha'),
                func.sum(Venta.total).label('totalVentas'),
                func.count(Venta.id).label('cantidadVentas')
            ).group_by('fecha').order_by('fecha')
        elif periodo == 'anual':
            q = db.session.query(
                func.extract('year', Venta.fecha_venta).cast(db.String).label('fecha'),
                func.sum(Venta.total).label('totalVentas'),
                func.count(Venta.id).label('cantidadVentas')
            ).group_by('fecha').order_by('fecha')
        else:
            return []

        result = q.all()
        # Convertir resultados a lista de dicts
        return [
            {
                'fecha': str(row.fecha),
                'totalVentas': float(row.totalVentas),
                'cantidadVentas': row.cantidadVentas
            }
            for row in result
        ]

    @staticmethod
    def top_clientes(limite=10):
        """
        Retorna lista con dicts {cliente: str, totalCompras: float}
        de los clientes con mayores compras totales.
        """
        q = db.session.query(
            Cliente.nombre.label('cliente'),
            func.sum(Venta.total).label('totalCompras')
        ).join(Venta, Venta.cliente_id == Cliente.id)\
         .group_by(Cliente.id)\
         .order_by(func.sum(Venta.total).desc())\
         .limit(limite)

        result = q.all()

        return [
            {
                'cliente': row.cliente,
                'totalCompras': float(row.totalCompras)
            }
            for row in result
        ]

    @staticmethod
    def ventas_cliente(cliente_id, periodo='diario'):
        """
        Retorna ventas de un cliente específico agrupadas por periodo
        igual a ventas_por_periodo pero filtrado por cliente_id
        """
        if periodo == 'diario':
            q = db.session.query(
                func.date(Venta.fecha_venta).label('fecha'),
                func.sum(Venta.total).label('totalVentas'),
                func.count(Venta.id).label('cantidadVentas')
            ).filter(Venta.cliente_id == cliente_id)\
             .group_by(func.date(Venta.fecha_venta))\
             .order_by(func.date(Venta.fecha_venta))
        elif periodo == 'mensual':
            q = db.session.query(
                func.concat(
                    func.extract('year', Venta.fecha_venta).cast(db.String),
                    '-',
                    func.lpad(func.extract('month', Venta.fecha_venta).cast(db.String), 2, '0')
                ).label('fecha'),
                func.sum(Venta.total).label('totalVentas'),
                func.count(Venta.id).label('cantidadVentas')
            ).filter(Venta.cliente_id == cliente_id)\
             .group_by('fecha')\
             .order_by('fecha')
        elif periodo == 'anual':
            q = db.session.query(
                func.extract('year', Venta.fecha_venta).cast(db.String).label('fecha'),
                func.sum(Venta.total).label('totalVentas'),
                func.count(Venta.id).label('cantidadVentas')
            ).filter(Venta.cliente_id == cliente_id)\
             .group_by('fecha')\
             .order_by('fecha')
        else:
            return []

        result = q.all()
        return [
            {
                'fecha': str(row.fecha),
                'totalVentas': float(row.totalVentas),
                'cantidadVentas': row.cantidadVentas
            }
            for row in result
        ]
        
    @staticmethod
    def resumen():
        hoy = date.today()
        mes_actual = hoy.month
        anio_actual = hoy.year

        # --- Ventas de hoy ---
        ventas_hoy = db.session.query(
            func.coalesce(func.sum(Venta.total), 0),
            func.count(Venta.id)
        ).filter(func.date(Venta.fecha_venta) == hoy).first()

        total_hoy = float(ventas_hoy[0])
        cant_hoy = ventas_hoy[1]
        ticket_hoy = total_hoy / cant_hoy if cant_hoy > 0 else 0

        # --- Ventas del mes ---
        ventas_mes = db.session.query(
            func.coalesce(func.sum(Venta.total), 0),
            func.count(Venta.id)
        ).filter(
            func.extract('month', Venta.fecha_venta) == mes_actual,
            func.extract('year', Venta.fecha_venta) == anio_actual
        ).first()

        total_mes = float(ventas_mes[0])
        cant_mes = ventas_mes[1]
        ticket_mes = total_mes / cant_mes if cant_mes > 0 else 0

        # --- Top productos (mes) ---
        top_productos = db.session.query(
            Producto.nombre,
            func.sum(DetalleVenta.cantidad).label('cantidad'),
            func.sum(DetalleVenta.cantidad * DetalleVenta.precio_unitario).label('total')
        ).join(Producto, DetalleVenta.producto_id == Producto.id) \
        .join(Venta, DetalleVenta.venta_id == Venta.id) \
        .filter(
            func.extract('month', Venta.fecha_venta) == mes_actual,
            func.extract('year', Venta.fecha_venta) == anio_actual
        ) \
        .group_by(Producto.nombre) \
        .order_by(func.sum(DetalleVenta.cantidad * DetalleVenta.precio_unitario).desc()) \
        .limit(5).all()

        top_productos_list = [
            {"producto": p[0], "cantidad": int(p[1]), "total": float(p[2])}
            for p in top_productos
        ]

        # --- Top clientes (mes) ---
        top_clientes = db.session.query(
            Cliente.nombre,
            func.sum(Venta.total).label('total')
        ).join(Cliente, Venta.cliente_id == Cliente.id) \
         .filter(
            func.extract('month', Venta.fecha_venta) == mes_actual,
            func.extract('year', Venta.fecha_venta) == anio_actual
         ) \
         .group_by(Cliente.nombre) \
         .order_by(func.sum(Venta.total).desc()) \
         .limit(5).all()

        top_clientes_list = [
            {"cliente": c[0], "total": float(c[1])}
            for c in top_clientes
        ]

        # --- Ventas por día (últimos 15 días) ---
        fecha_inicio = hoy - timedelta(days=15)
        ventas_por_dia = db.session.query(
            func.date(Venta.fecha_venta).label('fecha'),
            func.sum(Venta.total).label('total_ventas'),
            func.count(Venta.id).label('cantidad_ventas')
        ).filter(Venta.fecha_venta >= fecha_inicio) \
         .group_by(func.date(Venta.fecha_venta)) \
         .order_by(func.date(Venta.fecha_venta)).all()

        ventas_por_dia_list = [
            {
                "fecha": str(v[0]),
                "totalVentas": float(v[1]),
                "cantidadVentas": int(v[2])
            }
            for v in ventas_por_dia
        ]

        return {
            "ventas_hoy": {
                "total": total_hoy,
                "cantidad": cant_hoy,
                "ticket_promedio": ticket_hoy
            },
            "ventas_mes": {
                "total": total_mes,
                "cantidad": cant_mes,
                "ticket_promedio": ticket_mes
            },
            "top_productos": top_productos_list,
            "top_clientes": top_clientes_list,
            "ventas_por_dia": ventas_por_dia_list
        }
        
    @staticmethod
    def resumen_ingresos_egresos_diarios(fecha=None):
        if fecha is None:
            fecha = date.today()

        # Ingresos (ventas) del día
        ingresos = db.session.query(
            func.coalesce(func.sum(Venta.total), 0).label('total_ingresos'),
            func.count(Venta.id).label('cantidad_ventas')
        ).filter(func.date(Venta.fecha_venta) == fecha).one()

        # Subconsulta: total por pedido proveedor (detalle)
        total_por_pedido = (
            db.session.query(
                DetallePedidoProveedor.pedido_id.label('pedido_id'),
                func.sum(DetallePedidoProveedor.cantidad * DetallePedidoProveedor.precio_unitario).label('subtotal')
            )
            .group_by(DetallePedidoProveedor.pedido_id)
            .subquery()
        )

        # Egresos sumando subtotales de pedidos del día
        egresos = (
            db.session.query(
                func.coalesce(func.sum(total_por_pedido.c.subtotal), 0).label('total_egresos'),
                func.count(PedidoProveedor.id).label('cantidad_pedidos')
            )
            .join(total_por_pedido, PedidoProveedor.id == total_por_pedido.c.pedido_id)
            .filter(func.date(PedidoProveedor.fecha_pedido) == fecha)
            .one()
        )

        return {
            "fecha": fecha.isoformat(),
            "ingresos": {
                "total": float(ingresos.total_ingresos),
                "cantidad": ingresos.cantidad_ventas
            },
            "egresos": {
                "total": float(egresos.total_egresos),
                "cantidad": egresos.cantidad_pedidos
            }
        }
        
    @staticmethod
    def ganancia_mensual():
        resultados = (
            db.session.query(
                func.extract("year", Venta.fecha_venta).label("anio"),
                func.extract("month", Venta.fecha_venta).label("mes"),
                func.sum(DetalleVenta.cantidad * DetalleVenta.precio_unitario).label("total_ventas"),
                func.sum(DetalleVenta.cantidad * Producto.precio_ars).label("total_costos"),
            )
            .join(DetalleVenta, DetalleVenta.venta_id == Venta.id)
            .join(Producto, Producto.id == DetalleVenta.producto_id)
            .group_by("anio", "mes")
            .order_by("anio", "mes")
            .all()
        )

        data = []
        for r in resultados:
            total_ventas = float(r.total_ventas or 0)
            total_costos = float(r.total_costos or 0)
            ganancia = total_ventas - total_costos
            data.append({
                "mes": f"{int(r.anio)}-{int(r.mes):02d}",
                "totalVentas": total_ventas,
                "totalCostos": total_costos,
                "gananciaNeta": ganancia
            })

        return data