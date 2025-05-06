from datetime import datetime, timezone
from app import db

class Proveedor(db.Model):
    __tablename__ = 'proveedores'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(200), unique=True, nullable=False)
    codigo_proveedor = db.Column(db.String(50), unique=True, nullable=False)
    sitio_web = db.Column(db.String(255), nullable=True)
    porcentaje_ganancia = db.Column(db.Float, nullable=False, default=0)
    precio_con_iva = db.Column(db.Boolean, default=True)
    descripcion = db.Column(db.String(255), nullable=True)
    direccion = db.Column(db.String(255), nullable=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))

    status_id = db.Column(db.Integer, db.ForeignKey('status.id'), nullable=False)
    status = db.relationship('Status', backref=db.backref('proveedores', lazy=True))
    pedidos = db.relationship('PedidoProveedor', back_populates='proveedor', lazy=True)
    productos = db.relationship('Producto', back_populates='proveedor', lazy=True)

    # Aquí usamos 'Vendedor' como cadena en lugar de referencia directa
    vendedores_rel = db.relationship('Vendedor', back_populates='proveedor', lazy=True)

    def serialize(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'codigo_proveedor': self.codigo_proveedor,
            'sitio_web': self.sitio_web,
            'vendedores': [vendedor.serialize() for vendedor in self.vendedores_rel],
            'porcentaje_ganancia': self.porcentaje_ganancia,
            'precio_con_iva': self.precio_con_iva,
            'descripcion': self.descripcion,
            'direccion': self.direccion,
            'fecha_creacion': self.fecha_creacion.isoformat(),
            'fecha_actualizacion': self.fecha_actualizacion.isoformat(),
            'status_id': self.status_id,
            'status': self.status.serialize() if self.status else None
        }

    def __repr__(self):
        return f'<Proveedor {self.nombre} - {self.codigo_proveedor}>'
