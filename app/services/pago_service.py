from decimal import Decimal

from sqlalchemy import func
from app.models import Pago
from app import db
from datetime import datetime, timezone
from app.models.cliente import Cliente
from app.models.venta import Venta
from app.services.status_service import StatusService
from app.models.movimiento_cliente import MovimientoCliente, TipoMovimientoCliente
from app.services.ventas_service import VentaService

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
    ):
        cliente = Cliente.query.get_or_404(cliente_id)

        monto_ingresado = Decimal(str(monto))
        credito_disponible = VentaService.obtener_credito_disponible(cliente_id)

        total_disponible = monto_ingresado + credito_disponible

        # 1️⃣ Pago (UNO SOLO)
        pago = Pago(
            cliente_id=cliente_id,
            monto=monto_ingresado,
            forma_pago_id=forma_pago_id,
            observaciones=observaciones
        )
        db.session.add(pago)

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
        credito_restante = credito_disponible
        credito_usado_total = Decimal("0")

        for venta in ventas_pendientes:
            if restante <= 0:
                break

            saldo_venta = Decimal(venta.total) - Decimal(venta.pagado)

            aplicado = min(restante, saldo_venta)

            venta.pagado += aplicado
            restante -= aplicado

            # 🔥 calcular cuánto de esto fue crédito
            usado_credito = min(aplicado, credito_restante)
            credito_restante -= usado_credito
            credito_usado_total += usado_credito

            if venta.pagado >= venta.total:
                estado_pagada = StatusService.get_status_by_code("charged")
                if estado_pagada:
                    venta.estado_id = estado_pagada.id

            venta.actualizar_saldo()

            db.session.add(MovimientoCliente(
                cliente_id=cliente_id,
                tipo=TipoMovimientoCliente.PAGO,
                monto=aplicado,
                venta_id=venta.id,
                pago=pago,
                observaciones=f"Aplicación pago a venta #{venta.id}"
            ))

        # 🔥 registrar uso de crédito
        if credito_usado_total > 0:
            db.session.add(MovimientoCliente(
                cliente_id=cliente_id,
                tipo=TipoMovimientoCliente.USO_CREDITO,
                monto=credito_usado_total,
                observaciones="Uso de crédito disponible"
            ))

            # 🔥 actualizar cache
            cliente.saldo_favor = (cliente.saldo_favor or Decimal("0")) - credito_usado_total

        # 3️⃣ si sobra → nuevo crédito
        if restante > 0:
            db.session.add(MovimientoCliente(
                cliente_id=cliente_id,
                tipo=TipoMovimientoCliente.CREDITO,
                monto=restante,
                pago=pago,
                observaciones="Saldo a favor generado"
            ))

            # 🔥 actualizar cache
            cliente.saldo_favor = (cliente.saldo_favor or Decimal("0")) + restante

        db.session.commit()

        return pago, float(restante)