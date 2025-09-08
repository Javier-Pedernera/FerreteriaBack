from datetime import datetime, timezone
from app import db
from app.models import MovimientoCuenta, Cuenta, Status

class MovimientoService:

    @staticmethod
    def get_movimientos(cuenta_id):
        return [m.serialize() for m in MovimientoCuenta.query.filter_by(cuenta_id=cuenta_id).all()]

    @staticmethod
    def create_movimiento(cuenta_id, data):
        cuenta = Cuenta.query.get_or_404(cuenta_id)

        # Ajusta el saldo
        if data['tipo'] == 'ingreso':
            cuenta.saldo += data['monto']
        elif data['tipo'] == 'egreso':
            cuenta.saldo -= data['monto']
        elif data['tipo'] == 'transferencia':
            cuenta.saldo -= data['monto']
            if not data.get('cuenta_destino_id'):
                raise Exception("Debe indicar cuenta destino para transferencia")
            destino = Cuenta.query.get_or_404(data['cuenta_destino_id'])
            destino.saldo += data['monto']
        else:
            raise Exception("Tipo de movimiento no válido")

        movimiento = MovimientoCuenta(
            cuenta_id=cuenta_id,
            tipo=data['tipo'],
            descripcion=data.get('descripcion'),
            monto=data['monto'],
            fecha=datetime.now(timezone.utc),
            status_id=data['status_id'],
            cuenta_destino_id=data.get('cuenta_destino_id')
        )
        db.session.add(movimiento)
        db.session.commit()
        return movimiento.serialize()
