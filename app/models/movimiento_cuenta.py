from datetime import datetime, timezone
from .. import db

class MovimientoCuenta(db.Model):
    __tablename__ = 'movimientos_cuenta'

    id = db.Column(db.Integer, primary_key=True)
    cuenta_id = db.Column(db.Integer, db.ForeignKey('cuentas.id'), nullable=False)
    cuenta_destino_id = db.Column(db.Integer, db.ForeignKey('cuentas.id'), nullable=True)  # Para transferencias
    tipo = db.Column(db.String(20), nullable=False)  # 'ingreso', 'egreso', 'transferencia'
    descripcion = db.Column(db.String(200), nullable=True)
    monto = db.Column(db.Float, nullable=False)
    fecha = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    status_id = db.Column(db.Integer, db.ForeignKey('status.id'), nullable=False)

    cuenta = db.relationship('Cuenta', foreign_keys=[cuenta_id], back_populates='movimientos', lazy=True)
    cuenta_destino = db.relationship('Cuenta', foreign_keys=[cuenta_destino_id], lazy=True)
    status = db.relationship('Status', lazy=True)

    def serialize(self):
        return {
            "id": self.id,
            "cuenta_id": self.cuenta_id,
            "cuenta_destino_id": self.cuenta_destino_id,
            "tipo": self.tipo,
            "descripcion": self.descripcion,
            "monto": self.monto,
            "fecha": self.fecha.isoformat() if self.fecha else None,
            "status": self.status.label if self.status else None,
        }
