from datetime import datetime, timezone
from app import db
from app.models import Cuenta, MovimientoCuenta, Status

class CuentaService:

    @staticmethod
    def get_all_cuentas():
        return [c.serialize() for c in Cuenta.query.all()]

    @staticmethod
    def get_cuenta_by_id(cuenta_id):
        return Cuenta.query.get_or_404(cuenta_id).serialize()

    @staticmethod
    def create_cuenta(data):
        nueva = Cuenta(
            nombre=data['nombre'],
            saldo=data.get('saldo', 0),
            moneda=data.get('moneda', 'ARS'),
            titular=data['titular'],
            cbu=data.get('cbu'),
            alias=data.get('alias'),
            status_id=data['status_id'],
            fecha_creacion=datetime.now(timezone.utc)
        )
        db.session.add(nueva)
        db.session.commit()
        return nueva.serialize()

    @staticmethod
    def update_cuenta(cuenta_id, data):
        cuenta = Cuenta.query.get_or_404(cuenta_id)
        for key, value in data.items():
            setattr(cuenta, key, value)
        db.session.commit()
        return cuenta.serialize()
