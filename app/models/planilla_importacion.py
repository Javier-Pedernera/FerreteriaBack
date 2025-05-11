from datetime import datetime, timezone
from app import db

class PlantillaImportacion(db.Model):
    __tablename__ = 'plantillas_importacion'

    id = db.Column(db.Integer, primary_key=True)
    proveedor_id = db.Column(db.Integer, db.ForeignKey('proveedores.id'), nullable=False, unique=True)
    nombre_archivo_excel = db.Column(db.String(200), nullable=False)
    nombre_columna_codigo = db.Column(db.String(100), nullable=False)
    nombre_columna_precio = db.Column(db.String(100), nullable=False)
    nombre_columna_precio_sugerido = db.Column(db.String(100), nullable=True)
    nombre_columna_nombre = db.Column(db.String(100), nullable=True)
    nombre_columna_descripcion = db.Column(db.String(100), nullable=True)
    nombre_columna_marca = db.Column(db.String(100), nullable=True)
    nombre_columna_categoria = db.Column(db.String(100), nullable=True)
    fila_inicio = db.Column(db.Integer, default=2)
    delimitador_decimal = db.Column(db.String(1), default='.')
    usa_simbolo_pesos = db.Column(db.Boolean, default=True)
    usa_miles_con_punto = db.Column(db.Boolean, default=True)
    fecha_ultima_lista = db.Column(db.DateTime, nullable=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    cod_solo_numero = db.Column(db.Boolean, default=False)
    
    proveedor = db.relationship('Proveedor', backref='plantillas_importacion', lazy=True)

    def serialize(self):
        return {
            'id': self.id,
            'proveedor_id': self.proveedor_id,
            'proveedor_nombre': self.proveedor.nombre if self.proveedor else None,
            'nombre_archivo_excel': self.nombre_archivo_excel,
            'nombre_columna_descripcion': self.nombre_columna_descripcion,
            'nombre_columna_codigo': self.nombre_columna_codigo,
            'nombre_columna_precio': self.nombre_columna_precio,
            'nombre_columna_precio_sugerido': self.nombre_columna_precio_sugerido,
            'nombre_columna_nombre': self.nombre_columna_nombre,
            'nombre_columna_marca': self.nombre_columna_marca,
            'nombre_columna_categoria': self.nombre_columna_categoria,
            'fila_inicio': self.fila_inicio,
            'delimitador_decimal': self.delimitador_decimal,
            'usa_simbolo_pesos': self.usa_simbolo_pesos,
            'usa_miles_con_punto': self.usa_miles_con_punto,
            'cod_solo_numero': self.cod_solo_numero,
            'fecha_creacion': self.fecha_creacion.isoformat(),
            'fecha_actualizacion': self.fecha_actualizacion.isoformat(),
            'fecha_ultima_lista': self.fecha_ultima_lista.isoformat() if self.fecha_ultima_lista else None
        }

    def __repr__(self):
        return f'<PlantillaImportacion proveedor_id={self.proveedor_id}>'
