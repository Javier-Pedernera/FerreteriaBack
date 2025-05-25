from app import db

class DetallePedidoProveedor(db.Model):
    __tablename__ = 'detalle_pedido_proveedor'

    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedidos_proveedor.id'), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(db.Numeric, nullable=False)
    unidades_por_presentacion = db.Column(db.Integer, nullable=False, default=1)
    
    producto = db.relationship('Producto', back_populates='detalles', lazy=True)
    pedido = db.relationship('PedidoProveedor', back_populates='detalles', lazy=True)

    def serialize(self):
        unidades_total = self.cantidad * self.unidades_por_presentacion
        return {
            "id": self.id,
            "pedido_id": self.pedido_id,
            "producto_id": self.producto_id,
            "producto": self.producto.nombre if self.producto else None,
            "cod_interno": self.producto.cod_interno if self.producto else None,
            "cantidad": self.cantidad,
            "precio_unitario": str(self.precio_unitario),
            "unidades_por_presentacion": self.unidades_por_presentacion,
            "subtotal": round(float(self.precio_unitario) * self.cantidad, 2),
            "unidades_total": unidades_total
        }

    def __repr__(self):
        return f"<DetallePedidoProveedor {self.producto.nombre} - {self.cantidad} presentaciones>"
