from datetime import datetime, timedelta, timezone
from decimal import Decimal
from operator import and_

from sqlalchemy import func
from app import db
from app.models.cliente import Cliente
from app.models.forma_pago import FormaPago
from app.models.movimiento_cliente import MovimientoCliente, TipoMovimientoCliente
from app.models.pago import Pago
from app.models.usuario import Usuario
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
            cliente_id=data.get('cliente_id')  # 👈 sigue igual
        )

        db.session.add(venta)
        db.session.flush()  # obtener ID

        # =========================
        # DETALLES (SIN CAMBIOS)
        # =========================
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
            if precio_costo_unitario > 0:
                porcentaje = float(
                    ((precio_unitario - precio_costo_unitario) / precio_costo_unitario) * 100
                )

            detalle = DetalleVenta(
                venta_id=venta.id,
                producto_id=item['producto_id'],
                cantidad=int(item['cantidad']),
                precio_unitario=precio_unitario,
                precio_costo=precio_costo_unitario,
                porcentaje_ganancia_aplicado=porcentaje
            )

            db.session.add(detalle)

        # =========================
        # NUEVO SISTEMA (NO ROMPE NADA)
        # =========================
        if venta.cliente_id:

            movimiento = MovimientoCliente(
                cliente_id=venta.cliente_id,
                tipo=TipoMovimientoCliente.VENTA,
                monto=-Decimal(venta.total),
                venta_id=venta.id,
                observaciones="AUTO: venta creada"
            )

            db.session.add(movimiento)

        # =========================
        # COMMIT FINAL (igual que antes)
        # =========================
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

        # =========================
        # 🔹 ACTUALIZAR CAMPOS
        # =========================
        venta.cliente_id = data.get('cliente_id', venta.cliente_id)
        venta.total = Decimal(data.get('total', venta.total))
        venta.descuento = Decimal(data.get('descuento', venta.descuento or 0))
        venta.forma_pago_id = data.get('forma_pago_id', venta.forma_pago_id)
        venta.observaciones = data.get('observaciones', getattr(venta, 'observaciones', None))

        if 'pagado' in data:
            venta.pagado = Decimal(data['pagado'] or 0)

        venta.actualizar_saldo()

        # 🔹 Estado
        if venta.saldo <= 0:
            estado_pagada = StatusService.get_status_by_code('charged')
            if estado_pagada:
                venta.estado_id = estado_pagada.id
            if not venta.fecha_pago:
                venta.fecha_pago = datetime.now(timezone.utc)

        # =========================
        # 🔹 DETALLES
        # =========================
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

        # =========================
        # 🧠 MOVIMIENTO CLIENTE
        # =========================
        if venta.cliente_id:

            movimiento_base = MovimientoCliente.query.filter_by(
                venta_id=venta.id,
                tipo=TipoMovimientoCliente.VENTA
            ).first()

            nuevo_total = Decimal(venta.total or 0)
            nuevo_monto = -nuevo_total  # 🔥 CLAVE: SIEMPRE NEGATIVO

            if movimiento_base:
                monto_anterior = movimiento_base.monto

                movimiento_base.monto = nuevo_monto
                movimiento_base.observaciones = (
                    f"Actualizado de {monto_anterior} a {nuevo_monto}"
                )
            else:
                db.session.add(MovimientoCliente(
                    cliente_id=venta.cliente_id,
                    tipo=TipoMovimientoCliente.VENTA,
                    monto=nuevo_monto,  # 🔥 NEGATIVO
                    venta_id=venta.id,
                    observaciones="AUTO: reconstrucción de movimiento"
                ))

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

        total_ajustado = Decimal(venta.total) * (
            Decimal("1") - Decimal(descuento_aplicado) / Decimal("100")
        )

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

        # =========================
        # PAGO (SIEMPRE)
        # =========================
        if forma_pago.nombre.lower() != 'cuenta corriente':

            pago = Pago(
                cliente_id=venta.cliente_id,  # puede ser None ✔
                venta_id=venta.id, 
                monto=Decimal(monto_abonado),
                forma_pago_id=forma_pago_id,
                observaciones=observaciones or f"Pago venta #{venta.id}"
            )
            db.session.add(pago)

            # =========================
            # MOVIMIENTO (SOLO SI HAY CLIENTE)
            # =========================
            if venta.cliente_id:
                db.session.add(MovimientoCliente(
                    cliente_id=venta.cliente_id,
                    tipo=TipoMovimientoCliente.PAGO,
                    monto=Decimal(monto_abonado),
                    venta_id=venta.id,
                    pago=pago,
                    observaciones=f"Pago venta #{venta.id}"
                ))

        db.session.commit()
        return venta.serialize()
    
    @staticmethod
    def obtener_credito_disponible(cliente_id):
        creditos = db.session.query(
            func.coalesce(func.sum(MovimientoCliente.monto), 0)
        ).filter(
            MovimientoCliente.cliente_id == cliente_id,
            MovimientoCliente.tipo == TipoMovimientoCliente.CREDITO
        ).scalar()

        credito_usado = db.session.query(
            func.coalesce(func.sum(MovimientoCliente.monto), 0)
        ).filter(
            MovimientoCliente.cliente_id == cliente_id,
            MovimientoCliente.tipo == TipoMovimientoCliente.USO_CREDITO
        ).scalar()

        # credito_usado ya es negativo, por eso se suma
        return Decimal(creditos) + Decimal(credito_usado)
    
    
    # =========================================================================
# Agregar este import arriba de ventas_service.py, junto a los demás:
#   from app.models.cliente import Cliente
#   from app.models.usuario import Usuario   # ajustar el nombre si difiere
#
# Agregar este método DENTRO de la clase VentaService:
# =========================================================================

    @staticmethod
    def gestionar_devolucion(venta_id: int, data: dict) -> dict:
        """
        Devuelve parte o la totalidad de los productos de una venta.
        Si se devuelve todo, el total de la venta queda en 0.
    
        Si la venta ya tenía pago(s) registrado(s) (tabla `pagos`, vía el
        MovimientoCliente tipo PAGO ligado a esta venta) y el excedente generado
        por la devolución los cubre, se reducen o eliminan esos pagos para que
        reflejen la realidad (no se toca saldo_favor ni deuda del cliente).
    
        data esperado:
        {
            "usuario_id": 1,                      # opcional, solo para la nota
            "motivo": "Producto en mal estado",    # opcional
            "items": [
                {"producto_id": 10, "cantidad": 2}
            ]
        }
        """
        venta = Venta.query.get_or_404(venta_id)
    
        if venta.estado and venta.estado.code == 'deleted':
            raise ValueError("No se puede procesar una devolución de una venta eliminada")
    
        items = data.get('items') or []
        if not items:
            raise ValueError("Debe incluir al menos un item a devolver")
    
        motivo = data.get('motivo', '')
        usuario_id = data.get('usuario_id')
    
        detalles_map = {d.producto_id: d for d in venta.detalles}
    
        monto_devuelto_total = Decimal("0")
        resumen_items = []
    
        # =========================
        # 🔹 PROCESAR CADA ITEM DEVUELTO
        # =========================
        for item in items:
            producto_id = item.get('producto_id')
            cantidad_devuelta = Decimal(str(item.get('cantidad', 0)))
    
            if cantidad_devuelta <= 0:
                raise ValueError(f"Cantidad inválida para producto {producto_id}")
    
            detalle = detalles_map.get(producto_id)
            if not detalle:
                raise ValueError(f"El producto {producto_id} no pertenece a esta venta")
    
            if cantidad_devuelta > Decimal(str(detalle.cantidad)):
                raise ValueError(
                    f"No se puede devolver {cantidad_devuelta} de un producto "
                    f"del que solo se vendieron {detalle.cantidad}"
                )
    
            precio_unitario = Decimal(detalle.precio_unitario)
            monto_devuelto_total += cantidad_devuelta * precio_unitario
    
            nombre_producto = detalle.producto.nombre if detalle.producto else f"#{producto_id}"
            resumen_items.append(f"-{cantidad_devuelta} {nombre_producto}")
    
            # Reduce (o elimina) el detalle original
            nueva_cantidad = Decimal(str(detalle.cantidad)) - cantidad_devuelta
            if nueva_cantidad <= 0:
                db.session.delete(detalle)
            else:
                detalle.cantidad = nueva_cantidad
    
            # TODO: cuando esté funcionando el control de stock,
            # reponer acá: producto = Producto.query.get(producto_id); producto.disponibles += cantidad_devuelta
    
        # =========================
        # 🔹 RECALCULAR TOTAL DE LA VENTA
        # =========================
        nuevo_total = Decimal(venta.total) - monto_devuelto_total
        if nuevo_total < 0:
            nuevo_total = Decimal("0")
    
        venta.total = nuevo_total

        # 🔹 Si se devolvió todo, la venta queda anulada
        if nuevo_total == 0:
            estado_cancelado = Status.query.filter_by(code='cancelled').first()
            if estado_cancelado:
                venta.estado_id = estado_cancelado.id
        # =========================
        # 🔹 EXCEDENTE: si ya se había pagado más de lo que ahora corresponde,
        # ajustamos/eliminamos los Pago reales de esta venta
        # =========================
        diferencia = Decimal(venta.pagado or 0) - nuevo_total
    
        if diferencia > 0:
            monto_restante = diferencia

            if venta.cliente_id:
                # Cliente registrado: un mismo Pago puede haber cubierto varias ventas
                # (ej. registrar_pago_cliente). El MovimientoCliente(tipo=PAGO, venta_id=X)
                # nos dice cuánto de qué pago se aplicó específicamente a ESTA venta.
                movimientos_pago = MovimientoCliente.query.filter_by(
                    venta_id=venta.id,
                    tipo=TipoMovimientoCliente.PAGO
                ).order_by(MovimientoCliente.fecha.desc()).all()

                for mov_pago in movimientos_pago:
                    if monto_restante <= 0:
                        break

                    monto_aplicado_a_esta_venta = Decimal(mov_pago.monto)
                    pago = mov_pago.pago

                    reduccion = min(monto_restante, monto_aplicado_a_esta_venta)

                    # Reducimos lo que este pago había aplicado a ESTA venta puntual
                    nuevo_monto_mov = monto_aplicado_a_esta_venta - reduccion
                    if nuevo_monto_mov <= 0:
                        db.session.delete(mov_pago)
                    else:
                        mov_pago.monto = nuevo_monto_mov

                    # Reducimos el Pago real en la misma medida, sin importar
                    # si también cubrió otras ventas (no lo borramos si aún les queda)
                    if pago:
                        nuevo_monto_pago = Decimal(pago.monto) - reduccion
                        if nuevo_monto_pago <= 0:
                            db.session.delete(pago)
                        else:
                            pago.monto = nuevo_monto_pago

                    monto_restante -= reduccion

            else:
                # Cliente desconocido: el Pago está 1 a 1 con la venta (vía venta_id directo,
                # cargado en cobrar_venta), no hay reparto posible.
                pagos_venta = Pago.query.filter_by(venta_id=venta.id).order_by(Pago.fecha.desc()).all()

                for pago in pagos_venta:
                    if monto_restante <= 0:
                        break

                    monto_pago_actual = Decimal(pago.monto)

                    if monto_restante >= monto_pago_actual:
                        monto_restante -= monto_pago_actual
                        db.session.delete(pago)
                    else:
                        pago.monto = monto_pago_actual - monto_restante
                        monto_restante = Decimal("0")

            venta.pagado = nuevo_total
    
        # =========================
        # 🔹 ACTUALIZAR MOVIMIENTO DE VENTA (mismo patrón que actualizar_venta)
        # =========================
        if venta.cliente_id:
            movimiento_venta = MovimientoCliente.query.filter_by(
                venta_id=venta.id,
                tipo=TipoMovimientoCliente.VENTA
            ).first()
    
            nuevo_monto = -nuevo_total
    
            if movimiento_venta:
                movimiento_venta.monto = nuevo_monto
                movimiento_venta.observaciones = f"Actualizado por devolución (venta #{venta.id})"
            else:
                db.session.add(MovimientoCliente(
                    cliente_id=venta.cliente_id,
                    tipo=TipoMovimientoCliente.VENTA,
                    monto=nuevo_monto,
                    venta_id=venta.id,
                    observaciones="AUTO: reconstrucción de movimiento por devolución"
                ))
    
        # =========================
        # 🔹 NOTA EN OBSERVACIONES (rastro liviano, sin tabla nueva)
        # =========================
        usuario_nombre = None
        if usuario_id:
            usuario = Usuario.query.get(usuario_id)
            usuario_nombre = usuario.nombre if usuario else None
    
        fecha_str = datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M')
        nota = f"[Devolución {fecha_str}"
        if usuario_nombre:
            nota += f" - {usuario_nombre}"
        nota += f"] {', '.join(resumen_items)}"
        if motivo:
            nota += f". Motivo: {motivo}"
        if diferencia > 0:
            nota += f". Excedente ${diferencia} ajustado en los pagos de la venta"
    
        venta.observaciones = f"{venta.observaciones}\n{nota}" if venta.observaciones else nota
    
        db.session.commit()
        return venta.serialize()