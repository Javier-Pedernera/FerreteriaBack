from datetime import datetime, timezone
from app import db

class Usuario(db.Model):
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=True)
    telefono = db.Column(db.String(50), nullable=True)
    creado_en = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    estado_id = db.Column(db.Integer, db.ForeignKey('status.id'), nullable=False)

    ventas = db.relationship('Venta', back_populates='vendedor', lazy=True)
    estado = db.relationship('Status', lazy=True)

    def serialize(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "apellido": self.apellido,
            "email": self.email,
            "telefono": self.telefono,
            "creado_en": self.creado_en.isoformat(),
            "estado": self.estado.label if self.estado else None
        }
