from datetime import datetime, timezone
from app import db

class Producto(db.Model):
    __tablename__ = 'productos'

    id = db.Column(db.Integer, primary_key=True)
    cod_interno = db.Column(db.String(50), unique=True, nullable=False)
    cod_proveedor = db.Column(db.String(50))
    nombre = db.Column(db.String(200), nullable=False)
    nombre_corto = db.Column(db.String, nullable=True)
    descripcion = db.Column(db.Text, nullable=True)
    precio_ars = db.Column(db.Numeric, nullable=False)
    precio_usd = db.Column(db.Numeric, nullable=True)
    precio_sugerido = db.Column(db.Numeric, nullable=True)
    porcentaje_ganancia = db.Column(db.Float, nullable=True)
    precio_final = db.Column(db.Numeric, nullable=True) 
    disponibles = db.Column(db.Integer, default=0)
    fecha_creacion = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    fecha_actualizacion = db.Column(
        db.DateTime,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc)
    )

    proveedor_id = db.Column(db.Integer, db.ForeignKey('proveedores.id'), nullable=False)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categorias.id'), nullable=True)
    status_id = db.Column(db.Integer, db.ForeignKey('status.id'), nullable=False)
    unidad_medida_id = db.Column(db.Integer, db.ForeignKey('unidades_medida.id'), nullable=True)
    marca_id = db.Column(db.Integer, db.ForeignKey('marcas.id'), nullable=True)
    ubicacion_local = db.Column(db.String(50), nullable=True)
    detalles_venta = db.relationship('DetalleVenta', back_populates='producto', lazy=True)
    
    porcentaje_ganancia_personalizado = db.Column(db.Boolean, default=False)
    
    categoria = db.relationship('Categoria', back_populates='productos', lazy=True)
    proveedor = db.relationship('Proveedor', back_populates='productos', lazy=True)
    status = db.relationship('Status', lazy=True)
    unidad_medida = db.relationship('UnidadMedida', back_populates='productos', lazy=True)
    marca = db.relationship('Marca', back_populates='productos', lazy=True)
    imagenes = db.relationship('ImagenProducto', backref='producto', lazy=True)
    detalles = db.relationship('DetallePedidoProveedor', back_populates='producto', lazy=True)
    
    def calcular_precio_final(self):
        try:
            porcentaje = self.porcentaje_ganancia if self.porcentaje_ganancia_personalizado else self.proveedor.porcentaje_ganancia
            return round(float(self.precio_ars) * (1 + porcentaje / 100), 2)
        except Exception:
            return None
    
    def serialize(self):
        return {
            'id': self.id,
            'cod_interno': self.cod_interno,
            'cod_proveedor': self.cod_proveedor,
            'nombre': self.nombre,
            'nombre_corto': self.nombre_corto,
            'descripcion': self.descripcion,
            'precio_ars': str(self.precio_ars),
            'precio_usd': str(self.precio_usd) if self.precio_usd else None,
            'precio_sugerido': str(self.precio_sugerido) if self.precio_sugerido else None,
            'porcentaje_ganancia': self.porcentaje_ganancia,
            'porcentaje_ganancia_personalizado': self.porcentaje_ganancia_personalizado,
            'precio_final': str(self.precio_final) if self.precio_final else None,
            'disponibles': self.disponibles,
            'fecha_creacion': self.fecha_creacion.isoformat(),
            'fecha_actualizacion': self.fecha_actualizacion.isoformat(),
            'proveedor_id': self.proveedor_id,
            'categoria_id': self.categoria_id,
            'ubicacion_local': self.ubicacion_local,
            'status_id': self.status_id,
            'unidad_medida_id': self.unidad_medida_id,
            'marca_id': self.marca_id,
            'unidad_medida': self.unidad_medida.codigo if self.unidad_medida else None,
            'categoria': self.categoria.nombre if self.categoria else None,
            'status': self.status.label if self.status else None,
            'proveedor': self.proveedor.nombre if self.proveedor else None,
            'marca': self.marca.nombre if self.marca else None,
            'imagenes': [img.serialize() for img in self.imagenes]
        }

    def __repr__(self):
        return f'<Producto {self.nombre} - {self.cod_interno}>'
