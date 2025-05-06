from datetime import datetime, timezone
from app import db

class ImagenProducto(db.Model):
    __tablename__ = 'imagenes_productos'

    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(255), nullable=False)
    es_portada = db.Column(db.Boolean, default=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.now(timezone.utc))

    def serialize(self):
        return {
            'id': self.id,
            'url': self.url,
            'es_portada': self.es_portada,
            'producto_id': self.producto_id,
            'fecha_creacion': self.fecha_creacion.isoformat()
        }

    def __repr__(self):
        return f'<ImagenProducto {self.url} - Portada: {self.es_portada}>'