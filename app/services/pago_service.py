from decimal import Decimal
from app.models import Pago
from app import db
from datetime import datetime, timezone
from app.models.cliente import Cliente
from app.models.venta import Venta
from app.services.status_service import StatusService
from app.models.movimiento_cliente import MovimientoCliente, TipoMovimientoCliente

class PagoService:

    @staticmethod
    def get_all_pagos(cliente_id=None):
        query = Pago.query
        if cliente_id:
            query = query.filter_by(cliente_id=cliente_id)
        return query.all()

    @staticmethod
    def get_pago_by_id(pago_id):
        return Pago.query.get(pago_id)

    @staticmethod
    def create_pago(data):
        pago = Pago(
            cliente_id=data['cliente_id'],
            venta_id=data.get('venta_id'),
            monto=data['monto'],
            fecha=data.get('fecha', datetime.now(timezone.utc)),
            observaciones=data.get('observaciones')
        )
        db.session.add(pago)
        db.session.commit()
        return pago

    @staticmethod
    def update_pago(pago_id, data):
        pago = Pago.query.get(pago_id)
        if not pago:
            return None
        pago.monto = data.get('monto', pago.monto)
        pago.fecha = data.get('fecha', pago.fecha)
        pago.observaciones = data.get('observaciones', pago.observaciones)
        db.session.commit()
        return pago

    @staticmethod
    def delete_pago(pago_id):
        pago = Pago.query.get(pago_id)
        if not pago:
            return None
        db.session.delete(pago)
        db.session.commit()
        return pago
    
    @staticmethod
    def registrar_pago_cliente(
        cliente_id: int,
        monto: float,
        forma_pago_id: int = None,
        observaciones: str = None,
        usar_saldo_favor: bool = False
    ):
        cliente = Cliente.query.get_or_404(cliente_id)

        monto_ingresado = Decimal(str(monto))
        saldo_favor = Decimal(str(cliente.saldo_favor or 0))

        total_disponible = monto_ingresado
        if usar_saldo_favor:
            total_disponible += saldo_favor
            cliente.saldo_favor = Decimal("0")

        # 1️⃣ Pago tradicional (SISTEMA VIEJO)
        pago = Pago(
            cliente_id=cliente_id,
            monto=monto_ingresado,
            forma_pago_id=forma_pago_id,
            observaciones=observaciones
        )
        db.session.add(pago)

        # 🟡 1.1 MOVIMIENTO (NUEVO - AUDITORÍA)
        movimiento_pago = MovimientoCliente(
            cliente_id=cliente_id,
            tipo=TipoMovimientoCliente.PAGO,
            monto=monto_ingresado,
            pago=pago,
            observaciones=observaciones
        )
        db.session.add(movimiento_pago)

        # 2️⃣ Ventas pendientes
        estado_deleted = StatusService.get_status_by_code("deleted")

        ventas_pendientes = (
            Venta.query
            .filter_by(cliente_id=cliente_id)
            .filter(Venta.pagado < Venta.total)
            .filter(Venta.estado_id != estado_deleted.id)
            .order_by(Venta.fecha_venta)
            .all()
        )

        restante = total_disponible

        for venta in ventas_pendientes:
            saldo_venta = Decimal(venta.total) - Decimal(venta.pagado)

            if restante >= saldo_venta:
                venta.pagado += saldo_venta
                restante -= saldo_venta

                venta.actualizar_saldo()

                estado_pagada = StatusService.get_status_by_code("charged")
                if estado_pagada:
                    venta.estado_id = estado_pagada.id

                # 🟡 MOVIMIENTO VENTA (AUDITORÍA)
                db.session.add(MovimientoCliente(
                    cliente_id=cliente_id,
                    tipo=TipoMovimientoCliente.VENTA,
                    monto=-saldo_venta,
                    venta=venta,
                    observaciones="Aplicación de pago a venta"
                ))

            else:
                venta.pagado += restante

                db.session.add(MovimientoCliente(
                    cliente_id=cliente_id,
                    tipo=TipoMovimientoCliente.VENTA,
                    monto=-restante,
                    venta=venta,
                    observaciones="Pago parcial"
                ))

                restante = Decimal("0")
                venta.actualizar_saldo()
                break

        # 3️⃣ saldo a favor (legacy)
        if restante > 0:
            cliente.saldo_favor = (cliente.saldo_favor or Decimal("0")) + restante

            db.session.add(MovimientoCliente(
                cliente_id=cliente_id,
                tipo=TipoMovimientoCliente.CREDITO,
                monto=restante,
                observaciones="Saldo a favor generado"
            ))

        db.session.commit()

        return pago, float(restante)