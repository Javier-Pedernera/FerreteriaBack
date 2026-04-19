from app import db
from app.models import MovimientoCliente, TipoMovimientoCliente, Cliente
from decimal import Decimal


class ClienteFinanzasService:

    @staticmethod
    def recalcular_saldos(cliente_id: int):
        """
        🔥 FUENTE DE VERDAD NUEVA
        pero sincroniza sistema viejo
        """

        movimientos = MovimientoCliente.query.filter_by(
            cliente_id=cliente_id
        ).all()

        deuda = Decimal("0")
        credito = Decimal("0")

        for m in movimientos:
            if m.tipo == TipoMovimientoCliente.VENTA:
                deuda += m.monto

            elif m.tipo == TipoMovimientoCliente.PAGO:
                deuda -= m.monto

            elif m.tipo == TipoMovimientoCliente.CREDITO:
                credito += m.monto

            elif m.tipo == TipoMovimientoCliente.AJUSTE:
                deuda += m.monto

        saldo_final = deuda - credito

        # 🔥 sincronización con sistema viejo
        cliente = Cliente.query.get(cliente_id)
        cliente.saldo_favor = max(Decimal("0"), -saldo_final)

        db.session.commit()

        return {
            "deuda": float(deuda),
            "credito": float(credito),
            "saldo_final": float(saldo_final),
            "saldo_favor_legacy": float(cliente.saldo_favor)
        }
        