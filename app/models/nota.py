from datetime import datetime, timezone
from app import db

# Valores válidos para tipo_entidad y prioridad. Se validan a nivel de
# aplicación (NotaService) en vez de con un ENUM nativo de Postgres, para
# poder agregar tipos nuevos en el futuro sin necesitar una migración de
# ALTER TYPE.
TIPOS_ENTIDAD_NOTA = ('general', 'proveedor', 'producto', 'cliente', 'venta', 'pedido_proveedor')
PRIORIDADES_NOTA = ('baja', 'media', 'alta')


class Nota(db.Model):
    __tablename__ = 'notas'
    __table_args__ = (
        db.Index('ix_notas_tipo_entidad_entidad_id', 'tipo_entidad', 'entidad_id'),
        db.Index('ix_notas_usuario_asignado_id', 'usuario_asignado_id'),
        db.Index('ix_notas_fecha_recordatorio', 'fecha_recordatorio'),
    )

    id = db.Column(db.Integer, primary_key=True)

    titulo = db.Column(db.String(200), nullable=True)
    contenido = db.Column(db.Text, nullable=False)

    # Vínculo polimórfico: a qué entidad hace referencia la nota (opcional).
    # No es una FK real porque puede apuntar a distintas tablas.
    tipo_entidad = db.Column(db.String(30), nullable=False, default='general')
    entidad_id = db.Column(db.Integer, nullable=True)

    prioridad = db.Column(db.String(10), nullable=False, default='media')

    usuario_creador_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    usuario_asignado_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)

    leida = db.Column(db.Boolean, nullable=False, default=False)
    fecha_lectura = db.Column(db.DateTime, nullable=True)

    completada = db.Column(db.Boolean, nullable=False, default=False)
    fecha_completada = db.Column(db.DateTime, nullable=True)

    fecha_recordatorio = db.Column(db.DateTime, nullable=True)

    estado_id = db.Column(db.Integer, db.ForeignKey('status.id'), nullable=False)

    fecha_creacion = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    fecha_actualizacion = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    usuario_creador = db.relationship('Usuario', foreign_keys=[usuario_creador_id], lazy=True)
    usuario_asignado = db.relationship('Usuario', foreign_keys=[usuario_asignado_id], lazy=True)
    estado = db.relationship('Status', lazy=True)

    def serialize(self):
        return {
            'id': self.id,
            'titulo': self.titulo,
            'contenido': self.contenido,
            'tipo_entidad': self.tipo_entidad,
            'entidad_id': self.entidad_id,
            'prioridad': self.prioridad,
            'usuario_creador_id': self.usuario_creador_id,
            'usuario_creador': self.usuario_creador.nombre if self.usuario_creador else None,
            'usuario_asignado_id': self.usuario_asignado_id,
            'usuario_asignado': self.usuario_asignado.nombre if self.usuario_asignado else None,
            'leida': self.leida,
            'fecha_lectura': self.fecha_lectura.isoformat() if self.fecha_lectura else None,
            'completada': self.completada,
            'fecha_completada': self.fecha_completada.isoformat() if self.fecha_completada else None,
            'fecha_recordatorio': self.fecha_recordatorio.isoformat() if self.fecha_recordatorio else None,
            'estado': self.estado.code if self.estado else None,
            'fecha_creacion': self.fecha_creacion.isoformat(),
            'fecha_actualizacion': self.fecha_actualizacion.isoformat() if self.fecha_actualizacion else None,
        }

    def __repr__(self):
        return f'<Nota {self.id} {self.tipo_entidad}:{self.entidad_id}>'
