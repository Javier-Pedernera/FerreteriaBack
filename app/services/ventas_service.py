from datetime import datetime, timedelta, timezone
from operator import and_
from app import db
from app.models.venta import Venta
from app.models.detalle_venta import DetalleVenta
from app.models.status import Status

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
            detalle = DetalleVenta(
                venta_id=venta.id,
                producto_id=item['producto_id'],
                cantidad=item['cantidad'],
                precio_unitario=item['precio_unitario']
            )
            db.session.add(detalle)

        db.session.commit()
        return venta.serialize()

    @staticmethod
    def obtener_por_id(venta_id):
        venta = Venta.query.get(venta_id)
        if not venta:
            raise ValueError("Venta no encontrada")
        return venta.serialize()

    @staticmethod
    def obtener_todas():
        return [v.serialize() for v in Venta.query.order_by(Venta.fecha_venta.desc()).all()]

    @staticmethod
    def actualizar(venta_id, data):
        venta = Venta.query.get(venta_id)
        if not venta:
            raise ValueError("Venta no encontrada")

        venta.descuento = data.get('descuento', venta.descuento)
        venta.total = data.get('total', venta.total)
        venta.forma_pago_id = data.get('forma_pago_id', venta.forma_pago_id)
        venta.estado_id = data.get('estado_id', venta.estado_id)
        venta.cliente_id = data.get('cliente_id', venta.cliente_id)

        db.session.commit()
        return venta.serialize()

    @staticmethod
    def eliminar(venta_id):
        venta = Venta.query.get(venta_id)
        if not venta:
            raise ValueError("Venta no encontrada")
        db.session.delete(venta)
        db.session.commit()
        return {"message": "Venta eliminada correctamente"}

    @staticmethod
    def aplicar_pago_a_cuenta(cliente_id, monto_pagado):
        if monto_pagado <= 0:
            raise ValueError("El monto debe ser mayor a cero.")

        estado_en_cuenta = Status.query.filter_by(code='on_account').first()
        estado_pagado = Status.query.filter_by(code='paid').first()

        if not estado_en_cuenta or not estado_pagado:
            raise ValueError("Estados necesarios no encontrados.")

        ventas = Venta.query.filter_by(cliente_id=cliente_id, estado_id=estado_en_cuenta.id).order_by(Venta.fecha_venta).all()

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

        if estado_code:
            estado = Status.query.filter_by(code=estado_code).first()
            if estado:
                query = query.filter(Venta.estado_id == estado.id)

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

        paginado = query.order_by(Venta.fecha_venta.desc()).paginate(page=page, per_page=per_page, error_out=False)

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