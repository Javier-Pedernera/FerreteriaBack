from datetime import datetime, timezone
from app import db

class PedidoProveedor(db.Model):
    __tablename__ = 'pedidos_proveedor'

    id = db.Column(db.Integer, primary_key=True)
    fecha_pedido = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    proveedor_id = db.Column(db.Integer, db.ForeignKey('proveedores.id'), nullable=False)
    descuento = db.Column(db.Numeric, default=0)
    numero_factura = db.Column(db.String(100), nullable=True)
    estado_id = db.Column(db.Integer, db.ForeignKey('status.id'), nullable=False)
    fecha_llegada = db.Column(db.DateTime, nullable=True)
    fecha_pago = db.Column(db.DateTime, nullable=True)

    proveedor = db.relationship('Proveedor', back_populates='pedidos', lazy=True)
    detalles = db.relationship('DetallePedidoProveedor', back_populates='pedido', lazy=True)
    estado = db.relationship('Status', lazy=True)
    
    @property
    def total_estimado(self):
        return sum(detalle.cantidad * detalle.precio_unitario for detalle in self.detalles)

    @property
    def total_real(self):
        return self.total

    @property
    def total(self):
        total_sin_descuento = self.total_estimado
        return float(total_sin_descuento) - (float(total_sin_descuento) * (float(self.descuento) / 100))

    def actualizar_stock(self):
        if self.estado and self.estado.code == 'received':
            for detalle in self.detalles:
                detalle.producto.disponibles += detalle.cantidad
            db.session.commit()

    def serialize(self):
        return {
            "id": self.id,
            "fecha_pedido": self.fecha_pedido.isoformat(),
            "proveedor_id": self.proveedor_id,
            "proveedor": self.proveedor.nombre if self.proveedor else None,
            "estado_id": self.estado_id,
            "estado": self.estado.label if self.estado else None,
            "descuento": str(self.descuento),
            "total_estimado": round(self.total_estimado, 2),
            "total_real": round(self.total_real, 2),
            "total": round(self.total, 2),
            "fecha_llegada": self.fecha_llegada.isoformat() if self.fecha_llegada else None,
            "fecha_pago": self.fecha_pago.isoformat() if self.fecha_pago else None,
            "numero_factura": self.numero_factura,
            "detalles": [detalle.serialize() for detalle in self.detalles]
        }
