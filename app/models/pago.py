from datetime import datetime, timezone
from app import db

class Pago(db.Model):
    __tablename__ = 'pagos'

    id = db.Column(db.Integer, primary_key=True)

    fecha = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    monto = db.Column(db.Numeric(12, 2), nullable=False)

    cliente_id = db.Column(
        db.Integer,
        db.ForeignKey('clientes.id'),
        nullable=True
    )

    forma_pago_id = db.Column(
        db.Integer,
        db.ForeignKey('formas_pago.id'),
        nullable=True
    )

    observaciones = db.Column(db.Text, nullable=True)

    cliente = db.relationship('Cliente', back_populates='pagos', lazy=True)
    forma_pago = db.relationship('FormaPago', lazy=True)

    def serialize(self):
        return {
            "id": self.id,
            "fecha": self.fecha.isoformat(),
            "monto": str(self.monto),
            "cliente_id": self.cliente_id,
            "forma_pago": self.forma_pago.nombre if self.forma_pago else None,
            "observaciones": self.observaciones
        }