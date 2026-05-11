import enum
from datetime import datetime, timezone
from decimal import Decimal
from app import db


class TipoMovimientoCliente(enum.Enum):
    VENTA = "venta"
    PAGO = "pago"
    USO_CREDITO = "uso_credito"
    CREDITO = "credito"
    AJUSTE = "ajuste"


class MovimientoCliente(db.Model):
    __tablename__ = "movimientos_cliente"

    id = db.Column(db.Integer, primary_key=True)

    cliente_id = db.Column(db.Integer, db.ForeignKey("clientes.id"), nullable=False, index=True)

    tipo = db.Column(
        db.Enum(TipoMovimientoCliente, name="tipo_movimiento_cliente"),
        nullable=False,
        index=True
    )

    monto = db.Column(db.Numeric(12, 2), nullable=False)

    venta_id = db.Column(db.Integer, db.ForeignKey("ventas.id"), nullable=True)
    pago_id = db.Column(db.Integer, db.ForeignKey("pagos.id"), nullable=True)

    fecha = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    observaciones = db.Column(db.Text, nullable=True)

    cliente = db.relationship("Cliente", backref=db.backref("movimientos", lazy=True))
    venta = db.relationship("Venta", lazy=True)
    pago = db.relationship("Pago", lazy=True)

    def serialize(self):
        return {
            "id": self.id,
            "tipo": self.tipo.value,
            "monto": float(self.monto),
            "fecha": self.fecha.isoformat(),
            "observaciones": self.observaciones,
            "venta_id": self.venta_id,
            "pago_id": self.pago_id
        }