from sqlalchemy import func
from datetime import date, datetime, timedelta
from app import db
from app.models.status import Status
from app.models.venta import Venta
from app.models.cliente import Cliente
from app.models.detalle_venta import DetalleVenta
from app.models.producto import Producto
from app.models.pedido_proveedor import PedidoProveedor
from app.models.detalle_pedido_proveedor import DetallePedidoProveedor
from app.models.forma_pago import FormaPago
from app.models.categoria import Categoria


class EstadisticasService:

    # --------------------------------------------------
    # Total realmente ingresado por una venta: el bruto
    # (suma de detalles) neto del descuento aplicado.
    # El recargo de tarjeta no se suma aquí porque compensa
    # un costo (comisión de la tarjeta), no es ganancia.
    # El descuento se acota a [0, 100] para que una fila con
    # datos corruptos (ej. descuento guardado como monto, no
    # como %) no distorsione el resto de las estadísticas.
    # --------------------------------------------------
    @staticmethod
    def _descuento_frac_expr():
        descuento_acotado = func.least(func.greatest(func.coalesce(Venta.descuento, 0), 0), 100)
        return 1 - descuento_acotado / 100

    @staticmethod
    def _total_neto_expr():
        return Venta.total * EstadisticasService._descuento_frac_expr()

    # --------------------------------------------------
    # Aplica un filtro opcional de mes (formato "YYYY-MM") a
    # una query que ya tiene a Venta en su FROM/JOIN. Si mes
    # es None o vacío, no filtra (se mantiene el total general).
    # --------------------------------------------------
    @staticmethod
    def _filtrar_por_mes(query, mes):
        if not mes:
            return query
        try:
            anio_str, mes_str = mes.split('-')
            anio, mes_num = int(anio_str), int(mes_str)
        except (ValueError, AttributeError):
            return query
        return query.filter(
            func.extract('year', Venta.fecha_venta) == anio,
            func.extract('month', Venta.fecha_venta) == mes_num
        )

    # --------------------------------------------------
    # VENTAS POR PERÍODO (SOLO COBRADAS)
    # --------------------------------------------------
    @staticmethod
    def ventas_por_periodo(periodo='diario'):

        deleted_status_id = db.session.query(Status.id).filter(Status.code == 'deleted').scalar()
        total_neto = EstadisticasService._total_neto_expr()

        if periodo == 'diario':
            q = db.session.query(
                func.date(Venta.fecha_venta).label('fecha'),
                func.sum(total_neto).label('totalVentas'),
                func.count(Venta.id).label('cantidadVentas')
            ).filter(
                Venta.fecha_pago.isnot(None),
                Venta.estado_id != deleted_status_id   # 👈 SOLO ESTO
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
                func.sum(total_neto).label('totalVentas'),
                func.count(Venta.id).label('cantidadVentas')
            ).filter(
                Venta.fecha_pago.isnot(None),
                Venta.estado_id != deleted_status_id   # 👈 SOLO ESTO
            ).group_by('fecha').order_by('fecha')

        elif periodo == 'anual':
            q = db.session.query(
                func.extract('year', Venta.fecha_venta).cast(db.String).label('fecha'),
                func.sum(total_neto).label('totalVentas'),
                func.count(Venta.id).label('cantidadVentas')
            ).filter(
                Venta.fecha_pago.isnot(None),
                Venta.estado_id != deleted_status_id   # 👈 SOLO ESTO
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

        deleted_status_id = db.session.query(Status.id).filter(Status.code == 'deleted').scalar()
        total_neto = EstadisticasService._total_neto_expr()

        q = db.session.query(
            Cliente.nombre.label('cliente'),
            func.sum(total_neto).label('totalCompras')
        ).join(
            Venta, Venta.cliente_id == Cliente.id
        ).filter(
            Venta.fecha_pago.isnot(None),
            Venta.estado_id != deleted_status_id   # 👈
        ).group_by(
            Cliente.id
        ).order_by(
            func.sum(total_neto).desc()
        ).limit(limite)

        return [
            {
                'cliente': r.cliente,
                'totalCompras': float(r.totalCompras)
            }
            for r in q.all()
        ]

    # --------------------------------------------------
    # VENTAS POR FORMA DE PAGO (SOLO COBRADAS)
    # --------------------------------------------------
    @staticmethod
    def ventas_por_forma_pago(mes=None):

        deleted_status_id = db.session.query(Status.id).filter(Status.code == 'deleted').scalar()
        total_neto = EstadisticasService._total_neto_expr()

        q = db.session.query(
            FormaPago.nombre.label('formaPago'),
            func.sum(total_neto).label('total'),
            func.count(Venta.id).label('cantidad')
        ).join(
            Venta, Venta.forma_pago_id == FormaPago.id
        ).filter(
            Venta.fecha_pago.isnot(None),
            Venta.estado_id != deleted_status_id
        )
        q = EstadisticasService._filtrar_por_mes(q, mes)
        q = q.group_by(
            FormaPago.id
        ).order_by(
            func.sum(total_neto).desc()
        )

        resultados = [
            {
                'formaPago': r.formaPago,
                'total': float(r.total),
                'cantidad': r.cantidad
            }
            for r in q.all()
        ]

        total_general = sum(r['total'] for r in resultados)
        for r in resultados:
            r['porcentaje'] = round((r['total'] / total_general) * 100, 2) if total_general > 0 else 0

        return resultados

    # --------------------------------------------------
    # VENTAS POR CLIENTE
    # --------------------------------------------------
    @staticmethod
    def ventas_cliente(cliente_id, periodo='diario'):

        deleted_status_id = db.session.query(Status.id).filter(Status.code == 'deleted').scalar()
        total_neto = EstadisticasService._total_neto_expr()

        if periodo == 'diario':
            q = db.session.query(
                func.date(Venta.fecha_pago).label('fecha'),
                func.sum(total_neto).label('totalVentas'),
                func.count(Venta.id).label('cantidadVentas')
            ).filter(
                Venta.cliente_id == cliente_id,
                Venta.fecha_pago.isnot(None),
                Venta.estado_id != deleted_status_id   # 👈
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
                func.sum(total_neto).label('totalVentas'),
                func.count(Venta.id).label('cantidadVentas')
            ).filter(
                Venta.cliente_id == cliente_id,
                Venta.fecha_pago.isnot(None),
                Venta.estado_id != deleted_status_id   # 👈
            ).group_by('fecha').order_by('fecha')

        elif periodo == 'anual':
            q = db.session.query(
                func.extract('year', Venta.fecha_pago).cast(db.String).label('fecha'),
                func.sum(total_neto).label('totalVentas'),
                func.count(Venta.id).label('cantidadVentas')
            ).filter(
                Venta.cliente_id == cliente_id,
                Venta.fecha_pago.isnot(None),
                Venta.estado_id != deleted_status_id   # 👈
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
        total_neto = EstadisticasService._total_neto_expr()

        # Ventas hoy
        total_hoy, cant_hoy = db.session.query(
            func.coalesce(func.sum(total_neto), 0),
            func.count(Venta.id)
        ).join(
            Status, Status.id == Venta.estado_id
        ).filter(
            Venta.fecha_pago.isnot(None),
            Status.code != 'deleted',
            func.date(Venta.fecha_venta) == hoy
        ).first()

        # Ventas mes
        total_mes, cant_mes = db.session.query(
            func.coalesce(func.sum(total_neto), 0),
            func.count(Venta.id)
        ).join(
            Status, Status.id == Venta.estado_id
        ).filter(
            Venta.fecha_pago.isnot(None),
            Status.code != 'deleted',
            func.extract('month', Venta.fecha_venta) == mes,
            func.extract('year', Venta.fecha_venta) == anio
        ).first()

        # Top productos
        descuento_frac_linea = EstadisticasService._descuento_frac_expr()
        top_productos = db.session.query(
            Producto.nombre,
            func.sum(DetalleVenta.cantidad),
            func.sum(DetalleVenta.cantidad * DetalleVenta.precio_unitario * descuento_frac_linea)
        ).join(
            Producto, Producto.id == DetalleVenta.producto_id
        ).join(
            Venta, Venta.id == DetalleVenta.venta_id
        ).join(
            Status, Status.id == Venta.estado_id
        ).filter(
            Venta.fecha_pago.isnot(None),
            Status.code != 'deleted',
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
            func.sum(total_neto),
            func.count(Venta.id)
        ).join(
            Status, Status.id == Venta.estado_id
        ).filter(
            Venta.fecha_pago.isnot(None),
            Status.code != 'deleted',
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

        inicio = datetime.combine(fecha, datetime.min.time())
        fin = inicio + timedelta(days=1)
        total_neto = EstadisticasService._total_neto_expr()

        # 🔹 INGRESOS
        ingresos = db.session.query(
            func.coalesce(func.sum(total_neto), 0),
            func.count(Venta.id)
        ).join(
            Status, Status.id == Venta.estado_id
        ).filter(
            Venta.fecha_pago.isnot(None),
            Status.code != 'deleted',
            Venta.fecha_venta >= inicio,
            Venta.fecha_venta < fin
        ).one()

        # 🔹 EGRESOS
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
            PedidoProveedor.fecha_pedido >= inicio,
            PedidoProveedor.fecha_pedido < fin
        ).one()

        # 🔹 COSTO DE VENTAS
        costo_ventas = db.session.query(
            func.coalesce(
                func.sum(
                    DetalleVenta.cantidad * DetalleVenta.precio_costo
                ), 0
            )
        ).join(
            Venta, Venta.id == DetalleVenta.venta_id
        ).join(
            Status, Status.id == Venta.estado_id
        ).filter(
            Venta.fecha_pago.isnot(None),
            Status.code != 'deleted',
            Venta.fecha_venta >= inicio,
            Venta.fecha_venta < fin
        ).scalar() or 0

        return {
            "fecha": fecha.isoformat(),
            "ingresos": {
                "total": float(ingresos[0]),
                "cantidad": ingresos[1]
            },
            "egresos": {
                "total": float(egresos[0]),
                "cantidad": egresos[1]
            },
            "costoVentas": float(costo_ventas),
            "gananciaNeta": float(ingresos[0]) - float(costo_ventas)
        }

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
        # El descuento se aplica a nivel de venta (no por línea), así que para
        # repartirlo entre los productos vendidos cada línea se multiplica por
        # el mismo factor (1 - descuento/100) de su venta. El costo del
        # producto no se ve afectado por el descuento: el margen se reduce
        # exactamente por el monto descontado.
        descuento_frac = EstadisticasService._descuento_frac_expr()
        resultados = (
            db.session.query(
                func.extract('year', Venta.fecha_venta).label('anio'),
                func.extract('month', Venta.fecha_venta).label('mes'),
                func.sum(
                    DetalleVenta.cantidad * DetalleVenta.precio_unitario * descuento_frac
                ).label('total_ventas'),
                func.sum(
                    DetalleVenta.cantidad * DetalleVenta.precio_unitario * descuento_frac
                    - DetalleVenta.cantidad * DetalleVenta.precio_costo
                ).label('ganancia_neta'),
                # ✅ NUEVO
                func.avg(
                    DetalleVenta.porcentaje_ganancia_aplicado
                ).label('markup_promedio')
            )
            .join(DetalleVenta, DetalleVenta.venta_id == Venta.id)
            .join(Status, Status.id == Venta.estado_id)
            .filter(
                Venta.fecha_pago.isnot(None),
                Status.code != 'deleted'
            )
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
                ),
                "markupPromedio": (
                    round(float(r.markup_promedio), 2)
                    if r.markup_promedio is not None
                    else None
                ),
            }
            for r in resultados
        ]

    # --------------------------------------------------
    # PRODUCTOS MÁS VENDIDOS (SOLO COBRADAS)
    # --------------------------------------------------
    @staticmethod
    def productos_mas_vendidos(limite=10, mes=None):
        descuento_frac = EstadisticasService._descuento_frac_expr()

        q = (
            db.session.query(
                Producto.nombre.label('producto'),
                func.sum(DetalleVenta.cantidad).label('cantidad'),
                func.sum(
                    DetalleVenta.cantidad * DetalleVenta.precio_unitario * descuento_frac
                ).label('total')
            )
            .join(Producto, Producto.id == DetalleVenta.producto_id)
            .join(Venta, Venta.id == DetalleVenta.venta_id)
            .join(Status, Status.id == Venta.estado_id)
            .filter(
                Venta.fecha_pago.isnot(None),
                Status.code != 'deleted'
            )
        )
        q = EstadisticasService._filtrar_por_mes(q, mes)
        q = (
            q
            .group_by(Producto.id)
            .order_by(func.sum(DetalleVenta.cantidad * DetalleVenta.precio_unitario * descuento_frac).desc())
            .limit(limite)
        )

        return [
            {
                'producto': r.producto,
                'cantidad': float(r.cantidad),
                'total': float(r.total)
            }
            for r in q.all()
        ]

    # --------------------------------------------------
    # STOCK LENTO: productos con stock disponible que no
    # se vendieron (o casi no se vendieron) en los últimos
    # `dias` días.
    # --------------------------------------------------
    @staticmethod
    def stock_lento(dias=60, limite=15):
        desde = datetime.now() - timedelta(days=dias)
        deleted_status_id = db.session.query(Status.id).filter(Status.code == 'deleted').scalar()

        vendidos_recientes = (
            db.session.query(
                DetalleVenta.producto_id,
                func.sum(DetalleVenta.cantidad).label('cantidad_reciente')
            )
            .join(Venta, Venta.id == DetalleVenta.venta_id)
            .filter(
                Venta.fecha_pago.isnot(None),
                Venta.estado_id != deleted_status_id,
                Venta.fecha_venta >= desde
            )
            .group_by(DetalleVenta.producto_id)
            .subquery()
        )

        q = (
            db.session.query(
                Producto.nombre,
                Producto.disponibles,
                Categoria.nombre,
                func.coalesce(vendidos_recientes.c.cantidad_reciente, 0)
            )
            .outerjoin(vendidos_recientes, vendidos_recientes.c.producto_id == Producto.id)
            .outerjoin(Categoria, Categoria.id == Producto.categoria_id)
            .filter(
                Producto.disponibles > 0,
                func.coalesce(vendidos_recientes.c.cantidad_reciente, 0) == 0
            )
            .order_by(Producto.disponibles.desc())
            .limit(limite)
        )

        return [
            {
                'producto': r[0],
                'disponibles': r[1],
                'categoria': r[2],
            }
            for r in q.all()
        ]

    # --------------------------------------------------
    # MARGEN POR CATEGORÍA (SOLO COBRADAS)
    # --------------------------------------------------
    @staticmethod
    def margen_por_categoria(mes=None):
        descuento_frac = EstadisticasService._descuento_frac_expr()

        q = (
            db.session.query(
                func.coalesce(Categoria.nombre, 'Sin categoría').label('categoria'),
                func.sum(
                    DetalleVenta.cantidad * DetalleVenta.precio_unitario * descuento_frac
                ).label('total_ventas'),
                func.sum(
                    DetalleVenta.cantidad * DetalleVenta.precio_unitario * descuento_frac
                    - DetalleVenta.cantidad * DetalleVenta.precio_costo
                ).label('ganancia_neta')
            )
            .join(Producto, Producto.id == DetalleVenta.producto_id)
            .outerjoin(Categoria, Categoria.id == Producto.categoria_id)
            .join(Venta, Venta.id == DetalleVenta.venta_id)
            .join(Status, Status.id == Venta.estado_id)
            .filter(
                Venta.fecha_pago.isnot(None),
                Status.code != 'deleted'
            )
        )
        q = EstadisticasService._filtrar_por_mes(q, mes)
        q = (
            q
            .group_by(func.coalesce(Categoria.nombre, 'Sin categoría'))
            .order_by(func.sum(DetalleVenta.cantidad * DetalleVenta.precio_unitario * descuento_frac).desc())
        )

        return [
            {
                'categoria': r.categoria,
                'totalVentas': float(r.total_ventas),
                'gananciaNeta': float(r.ganancia_neta),
                'margen': (
                    round((float(r.ganancia_neta) / float(r.total_ventas)) * 100, 2)
                    if r.total_ventas and float(r.total_ventas) > 0
                    else 0
                )
            }
            for r in q.all()
        ]

    # --------------------------------------------------
    # CLIENTES FRECUENTES (por cantidad de compras) + ticket
    # promedio de cada uno (SOLO COBRADAS)
    # --------------------------------------------------
    @staticmethod
    def clientes_frecuentes(limite=10, mes=None):
        deleted_status_id = db.session.query(Status.id).filter(Status.code == 'deleted').scalar()
        total_neto = EstadisticasService._total_neto_expr()

        q = (
            db.session.query(
                Cliente.nombre.label('cliente'),
                func.count(Venta.id).label('cantidadCompras'),
                func.sum(total_neto).label('total')
            )
            .join(Venta, Venta.cliente_id == Cliente.id)
            .filter(
                Venta.fecha_pago.isnot(None),
                Venta.estado_id != deleted_status_id
            )
        )
        q = EstadisticasService._filtrar_por_mes(q, mes)
        q = (
            q
            .group_by(Cliente.id)
            .order_by(func.count(Venta.id).desc())
            .limit(limite)
        )

        return [
            {
                'cliente': r.cliente,
                'cantidadCompras': r.cantidadCompras,
                'total': float(r.total),
                'ticketPromedio': round(float(r.total) / r.cantidadCompras, 2) if r.cantidadCompras else 0
            }
            for r in q.all()
        ]

    # --------------------------------------------------
    # TICKET PROMEDIO GENERAL (todas las ventas cobradas)
    # --------------------------------------------------
    @staticmethod
    def ticket_promedio_general(mes=None):
        deleted_status_id = db.session.query(Status.id).filter(Status.code == 'deleted').scalar()
        total_neto = EstadisticasService._total_neto_expr()

        q = db.session.query(
            func.coalesce(func.sum(total_neto), 0),
            func.count(Venta.id)
        ).filter(
            Venta.fecha_pago.isnot(None),
            Venta.estado_id != deleted_status_id
        )
        q = EstadisticasService._filtrar_por_mes(q, mes)
        total, cantidad = q.first()

        return {
            'ticketPromedio': round(float(total) / cantidad, 2) if cantidad else 0,
            'cantidadVentas': cantidad
        }

    # --------------------------------------------------
    # CLIENTES INACTIVOS: tenían compras pero no volvieron
    # a comprar en los últimos `dias` días.
    # --------------------------------------------------
    @staticmethod
    def clientes_inactivos(dias=60, limite=15):
        deleted_status_id = db.session.query(Status.id).filter(Status.code == 'deleted').scalar()
        total_neto = EstadisticasService._total_neto_expr()
        corte = datetime.now() - timedelta(days=dias)

        q = (
            db.session.query(
                Cliente.nombre.label('cliente'),
                func.max(Venta.fecha_venta).label('ultimaCompra'),
                func.sum(total_neto).label('totalHistorico')
            )
            .join(Venta, Venta.cliente_id == Cliente.id)
            .filter(
                Venta.fecha_pago.isnot(None),
                Venta.estado_id != deleted_status_id
            )
            .group_by(Cliente.id)
            .having(func.max(Venta.fecha_venta) < corte)
            .order_by(func.sum(total_neto).desc())
            .limit(limite)
        )

        return [
            {
                'cliente': r.cliente,
                'ultimaCompra': r.ultimaCompra.date().isoformat(),
                'diasInactivo': (datetime.now() - r.ultimaCompra).days,
                'totalHistorico': float(r.totalHistorico)
            }
            for r in q.all()
        ]