from datetime import datetime, timezone
from app import db

class Venta(db.Model):
    __tablename__ = 'ventas'

    id = db.Column(db.Integer, primary_key=True)
    fecha_venta = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    fecha_pago = db.Column(db.DateTime, nullable=True)

    total = db.Column(db.Numeric, nullable=False)
    descuento = db.Column(db.Numeric, default=0)
    pagado = db.Column(db.Numeric, default=0)
    forma_pago_id = db.Column(db.Integer, db.ForeignKey('formas_pago.id'), nullable=True)
    estado_id = db.Column(db.Integer, db.ForeignKey('status.id'), nullable=False)

    vendedor_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=True)

    vendedor = db.relationship('Usuario', back_populates='ventas', lazy=True)
    cliente = db.relationship('Cliente', back_populates='ventas', lazy=True)
    forma_pago = db.relationship('FormaPago', lazy=True)
    estado = db.relationship('Status', lazy=True)

    detalles = db.relationship('DetalleVenta', back_populates='venta', lazy=True)

    def serialize(self):
        return {
            "id": self.id,
            "fecha_venta": self.fecha_venta.isoformat(),
            "fecha_pago": self.fecha_pago.isoformat() if self.fecha_pago else None,
            "total": str(self.total),
            "descuento": str(self.descuento),
            "pagado": str(self.pagado),
            "forma_pago": self.forma_pago.nombre if self.forma_pago else None,
            "estado": self.estado.label if self.estado else None,
            "vendedor": self.vendedor.nombre if self.vendedor else None,
            "cliente": self.cliente.nombre if self.cliente else None,
            "detalles": [detalle.serialize() for detalle in self.detalles]
        }
