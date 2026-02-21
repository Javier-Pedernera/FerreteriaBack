from app import db

class FacturaItem(db.Model):
    __tablename__ = "factura_items"

    id = db.Column(db.Integer, primary_key=True)

    factura_id = db.Column(
        db.Integer,
        db.ForeignKey("facturas.id"),
        nullable=False
    )

    producto_id = db.Column(
        db.Integer,
        db.ForeignKey("productos.id"),
        nullable=True
    )

    descripcion = db.Column(db.String(255), nullable=False)

    cantidad = db.Column(db.Numeric(12,3), nullable=False)

    precio_unitario = db.Column(db.Numeric(12,2), nullable=False)

    subtotal = db.Column(db.Numeric(14,2), nullable=False)

    iva_porcentaje = db.Column(db.Float, nullable=True)

    factura = db.relationship("Factura", back_populates="items")
    producto = db.relationship("Producto", lazy=True)

    def serialize(self):
        return {
            "id": self.id,
            "producto_id": self.producto_id,
            "descripcion": self.descripcion,
            "cantidad": float(self.cantidad),
            "precio_unitario": float(self.precio_unitario),
            "subtotal": float(self.subtotal),
            "iva_porcentaje": self.iva_porcentaje
        }