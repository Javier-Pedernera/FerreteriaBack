from datetime import datetime, timedelta, timezone
from decimal import Decimal
from operator import and_
from app import db
from app.models.forma_pago import FormaPago
from app.models.venta import Venta
from app.models.detalle_venta import DetalleVenta
from app.models.status import Status
from app.models.producto import Producto
from app.services.status_service import StatusService

class VentaService:

    @staticmethod
    def crear_venta(data):
        estado_inicial = Status.query.filter_by(code='in_progress').first()
        if not estado_inicial:
            raise ValueError("No se encontró el estado 'in_progress'")
        venta = Venta(
            fecha_venta=datetime.now(timezone.utc),
            total=data['total'],
            descuento=data.get('descuento', 0),
            forma_pago_id=data.get('forma_pago_id'),
            estado_id=estado_inicial.id,
            vendedor_id=data['vendedor_id'],
            cliente_id=data.get('cliente_id')
        )
        db.session.add(venta)
        db.session.flush()  # Necesario para obtener el ID antes del commit

        for item in data['detalles']:
            producto = Producto.query.get(item['producto_id'])
            if not producto:
                raise ValueError(f"Producto {item['producto_id']} no encontrado")

            if (
                producto.es_fraccionable and
                producto.presentacion_cantidad and
                producto.presentacion_cantidad > 0
            ):
                precio_costo_unitario = (
                    Decimal(producto.precio_ars) /
                    Decimal(producto.presentacion_cantidad)
                )
            else:
                precio_costo_unitario = Decimal(producto.precio_ars)
            precio_unitario = Decimal(item['precio_unitario'])

            porcentaje = None
            if precio_costo_unitario and precio_costo_unitario > 0:
                porcentaje = float(
                    ((precio_unitario - precio_costo_unitario) / precio_costo_unitario) * 100
                )
            detalle = DetalleVenta(
                venta_id=venta.id,
                producto_id=item['producto_id'],
                cantidad=int(item['cantidad']),
                precio_unitario=Decimal(item['precio_unitario']),
                precio_costo=precio_costo_unitario,
                porcentaje_ganancia_aplicado=porcentaje
            )

            db.session.add(detalle)

        db.session.commit()
        return venta.serialize()

    @staticmethod
    def obtener_por_id(venta_id):
        venta = Venta.query.get(venta_id)

        if not venta:
            raise ValueError("Venta no encontrada")

        if venta.estado and venta.estado.code == 'deleted':
            raise ValueError("Venta no encontrada")

        return venta.serialize()

    @staticmethod
    def obtener_todas():
        estado_deleted = Status.query.filter_by(code='deleted').first()

        query = Venta.query
        if estado_deleted:
            query = query.filter(Venta.estado_id != estado_deleted.id)

        return [
            v.serialize()
            for v in query.order_by(Venta.fecha_venta.desc()).all()
        ]

    def actualizar(venta_id, data):
        venta = Venta.query.get(venta_id)

        if not venta:
            raise ValueError("Venta no encontrada")

        if venta.estado and venta.estado.code == 'deleted':
            raise ValueError("No se puede actualizar una venta eliminada")

        venta.descuento = data.get('descuento', venta.descuento)
        venta.total = data.get('total', venta.total)
        venta.forma_pago_id = data.get('forma_pago_id', venta.forma_pago_id)
        venta.estado_id = data.get('estado_id', venta.estado_id)
        venta.cliente_id = data.get('cliente_id', venta.cliente_id)

        db.session.commit()
        return venta.serialize()

    @staticmethod
    def eliminar_logico(venta_id):
        venta = Venta.query.get(venta_id)
        if not venta:
            raise ValueError("Venta no encontrada")

        estado_deleted = Status.query.filter_by(code='deleted').first()
        if not estado_deleted:
            raise ValueError("Estado 'deleted' no encontrado")

        venta.estado_id = estado_deleted.id
        db.session.commit()

        return {"message": "Venta eliminada correctamente"}

    @staticmethod
    def aplicar_pago_a_cuenta(cliente_id, monto_pagado):
        if monto_pagado <= 0:
            raise ValueError("El monto debe ser mayor a cero.")

        estado_en_cuenta = Status.query.filter_by(code='on_account').first()
        estado_pagado = Status.query.filter_by(code='paid').first()
        estado_deleted = Status.query.filter_by(code='deleted').first()

        if not estado_en_cuenta or not estado_pagado:
            raise ValueError("Estados necesarios no encontrados.")

        ventas = Venta.query.filter_by(
            cliente_id=cliente_id,
            estado_id=estado_en_cuenta.id
        ).filter(
            Venta.estado_id != estado_deleted.id
        ).order_by(Venta.fecha_venta).all()

        resultado = []

        for venta in ventas:
            pendiente = float(venta.total) - float(venta.pagado or 0)

            if pendiente <= 0:
                continue

            if monto_pagado >= pendiente:
                venta.pagado = venta.total
                venta.estado_id = estado_pagado.id
                venta.fecha_pago = datetime.now(timezone.utc)
                monto_pagado -= pendiente
            else:
                venta.pagado = (venta.pagado or 0) + monto_pagado
                monto_pagado = 0

            resultado.append(venta.serialize())
            if monto_pagado <= 0:
                break

        db.session.commit()
        return resultado

    @staticmethod
    def obtener_filtradas(estado_code=None, fecha_str=None, page=1, per_page=10):
        query = Venta.query.join(Status, Venta.estado_id == Status.id)

        estado_deleted = Status.query.filter_by(code='deleted').first()

        # 1️⃣ Manejo del estado
        if estado_code:
            estado = Status.query.filter_by(code=estado_code).first()
            if not estado:
                raise ValueError(f"Estado '{estado_code}' no encontrado")

            query = query.filter(Venta.estado_id == estado.id)
        else:
            # ⚠️ Si NO se filtra por estado → excluir eliminadas
            if estado_deleted:
                query = query.filter(Venta.estado_id != estado_deleted.id)

        # 2️⃣ Filtro por fecha
        if fecha_str:
            try:
                fecha = datetime.strptime(fecha_str, '%Y-%m-%d')
                fecha_fin = fecha + timedelta(days=1)

                query = query.filter(and_(
                    Venta.fecha_venta >= fecha,
                    Venta.fecha_venta < fecha_fin
                ))
            except ValueError:
                raise ValueError("Formato de fecha inválido. Use YYYY-MM-DD")

        paginado = query.order_by(Venta.fecha_venta.desc()).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

        return {
            "data": [v.serialize() for v in paginado.items],
            "total_pages": paginado.pages,
            "current_page": paginado.page,
            "total_items": paginado.total
        }
    @staticmethod
    def cliente_tiene_venta_en_proceso(cliente_id: int) -> bool:
        estado = Status.query.filter(Status.code.ilike('in_progress')).first()
        if not estado:
            raise ValueError("Estado 'in_process' no encontrado")

        venta_en_proceso = (
            db.session.query(Venta)
            .filter(Venta.cliente_id == cliente_id, Venta.estado_id == estado.id)
            .first()
        )

        return venta_en_proceso is not None
    
    @staticmethod
    def actualizar_venta(venta_id: int, data: dict) -> Venta:
        venta = Venta.query.get_or_404(venta_id)

        # 🚫 Bloquear si está eliminada
        if venta.estado and venta.estado.code == 'deleted':
            raise ValueError("No se puede actualizar una venta eliminada")

        # Actualiza campos principales
        venta.cliente_id = data.get('cliente_id', venta.cliente_id)
        venta.total = Decimal(data.get('total', venta.total))
        venta.descuento = Decimal(data.get('descuento', venta.descuento or 0))
        venta.forma_pago_id = data.get('forma_pago_id', venta.forma_pago_id)
        venta.observaciones = data.get('observaciones', getattr(venta, 'observaciones', None))

        # 🔹 Solo actualizar pagado si viene en data
        if 'pagado' in data:
            venta.pagado = Decimal(data['pagado'] or 0)

        # 🔹 Actualizar saldo correctamente
        venta.actualizar_saldo()

        # 🔹 Si se pagó todo, poner fecha_pago y estado "charged"
        if venta.saldo <= 0:
            estado_pagada = StatusService.get_status_by_code('charged')
            if estado_pagada:
                venta.estado_id = estado_pagada.id
            if not venta.fecha_pago:
                venta.fecha_pago = datetime.now(timezone.utc)

        # Manejo de detalles
        nuevos_detalles = data.get('detalles', [])
        existentes_map = {d.producto_id: d for d in venta.detalles}
        nuevos_ids = {d['producto_id'] for d in nuevos_detalles}

        for producto_id in list(existentes_map):
            if producto_id not in nuevos_ids:
                db.session.delete(existentes_map[producto_id])

        for d in nuevos_detalles:
            producto_id = d['producto_id']
            cantidad = d['cantidad']
            precio_unitario = Decimal(d['precio_unitario'])

            if producto_id in existentes_map:
                detalle = existentes_map[producto_id]
                detalle.cantidad = cantidad
                detalle.precio_unitario = precio_unitario
            else:
                producto = Producto.query.get(producto_id)
                if not producto:
                    raise ValueError(f"Producto {producto_id} no encontrado")

                precio_costo_unitario = (
                    Decimal(producto.precio_ars) / Decimal(producto.presentacion_cantidad)
                    if producto.es_fraccionable and producto.presentacion_cantidad
                    else Decimal(producto.precio_ars)
                )

                nuevo_detalle = DetalleVenta(
                    venta_id=venta.id,
                    producto_id=producto_id,
                    cantidad=cantidad,
                    precio_unitario=precio_unitario,
                    precio_costo=precio_costo_unitario
                )
                db.session.add(nuevo_detalle)

        db.session.commit()
        return venta
    
    @staticmethod
    def cobrar_venta(
        venta_id,
        forma_pago_id,
        monto_abonado,
        persona_autorizada_id=None,
        observaciones=None,
        recargo_tarjeta=0,
        descuento_aplicado=0
    ):
        venta = Venta.query.get_or_404(venta_id)

        # 🚫 NO operar si está eliminada
        if venta.estado and venta.estado.code == 'deleted':
            raise ValueError("No se puede cobrar una venta eliminada")

        forma_pago = FormaPago.query.get_or_404(forma_pago_id)

        total_ajustado = Decimal(venta.total) * (Decimal("1") - Decimal(descuento_aplicado) / Decimal("100"))

        if forma_pago.nombre.lower() == 'cuenta corriente':
            venta.pagado = Decimal("0")
            venta.fecha_pago = None
            estado_code = 'on_account'
        else:
            if Decimal(monto_abonado) < total_ajustado:
                raise Exception("El monto abonado no cubre el total")

            venta.pagado = Decimal(monto_abonado)
            estado_code = 'charged'

        venta.actualizar_saldo()

        venta.forma_pago_id = forma_pago_id

        if persona_autorizada_id:
            venta.persona_autorizada_id = persona_autorizada_id

        if observaciones is not None:
            venta.observaciones = observaciones

        venta.recargo_tarjeta = Decimal(recargo_tarjeta)
        venta.descuento = Decimal(descuento_aplicado)

        nuevo_estado = Status.query.filter_by(code=estado_code).first()
        if not nuevo_estado:
            raise Exception(f"Estado '{estado_code}' no encontrado")

        venta.estado_id = nuevo_estado.id

        db.session.commit()
        return venta.serialize()