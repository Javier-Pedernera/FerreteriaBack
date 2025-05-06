from app import db

class DetalleVenta(db.Model):
    __tablename__ = 'detalles_venta'

    id = db.Column(db.Integer, primary_key=True)
    venta_id = db.Column(db.Integer, db.ForeignKey('ventas.id'), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)

    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(db.Numeric, nullable=False)

    venta = db.relationship('Venta', back_populates='detalles', lazy=True)
    producto = db.relationship('Producto', back_populates='detalles_venta', lazy=True)

    def serialize(self):
        return {
            "producto_id": self.producto_id,
            "producto": self.producto.nombre if self.producto else None,
            "cantidad": self.cantidad,
            "precio_unitario": str(self.precio_unitario),
            "subtotal": str(self.cantidad * self.precio_unitario)
        }
