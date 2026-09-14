from datetime import datetime, timezone
from app import db

# Posición dentro de la secuencia que se muestra en el TV:
#   intro     -> logo/video de apertura (se espera un único activo)
#   carrusel  -> piezas que rotan en el medio, en orden
#   outro     -> logo/video de cierre (se espera un único activo)
POSICIONES_ANUNCIO = ('intro', 'carrusel', 'outro')
TIPOS_ANUNCIO = ('imagen', 'video')

DURACION_IMAGEN_DEFAULT_MS = 8000


class Anuncio(db.Model):
    __tablename__ = 'anuncios'
    __table_args__ = (
        db.Index('ix_anuncios_posicion_orden', 'posicion', 'orden'),
    )

    id = db.Column(db.Integer, primary_key=True)

    posicion = db.Column(db.String(20), nullable=False, default='carrusel')
    tipo = db.Column(db.String(10), nullable=False)

    url = db.Column(db.String(500), nullable=False)
    titulo = db.Column(db.String(200), nullable=True)  # referencia interna, no se muestra en el TV

    # Solo aplica para tipo='imagen'; un video se muestra hasta que termina.
    duracion_ms = db.Column(db.Integer, nullable=True)

    orden = db.Column(db.Integer, nullable=False, default=0)
    activo = db.Column(db.Boolean, nullable=False, default=True)

    fecha_creacion = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    fecha_actualizacion = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def serialize(self):
        return {
            'id': self.id,
            'posicion': self.posicion,
            'tipo': self.tipo,
            'url': self.url,
            'titulo': self.titulo,
            'duracion_ms': self.duracion_ms if self.tipo == 'imagen' else None,
            'orden': self.orden,
            'activo': self.activo,
            'fecha_creacion': self.fecha_creacion.isoformat(),
            'fecha_actualizacion': self.fecha_actualizacion.isoformat() if self.fecha_actualizacion else None,
        }

    def serialize_publico(self):
        """Lo mínimo que necesita la pantalla del TV para mostrar la pieza."""
        data = {'tipo': self.tipo, 'url': self.url}
        if self.tipo == 'imagen':
            data['duracion_ms'] = self.duracion_ms or DURACION_IMAGEN_DEFAULT_MS
        return data

    def __repr__(self):
        return f'<Anuncio {self.id} {self.posicion}:{self.tipo}>'
