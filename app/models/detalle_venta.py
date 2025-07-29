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
        producto = self.producto
        print(producto)
        return {
        "producto_id": self.producto_id,
        "producto": getattr(producto, "nombre", None),
        "cod_interno": getattr(producto, "cod_interno", None),
        "precio_costo": getattr(producto, "precio_ars", None),
        "presentacion_cantidad": getattr(producto, "presentacion_cantidad", None),
        "unidad_medida": getattr(producto, "unidad_medida.codigo", None) if producto and producto.unidad_medida else None,
        "disponibles": getattr(producto, "disponibles", None),
        "cantidad": self.cantidad,
        "precio_unitario": str(self.precio_unitario),
        "subtotal": str(self.cantidad * self.precio_unitario)
    }
# git commit -m "agrego el codigo interno al detalle" 