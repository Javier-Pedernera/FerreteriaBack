from datetime import datetime, timezone
from app import db

class Cliente(db.Model):
    __tablename__ = 'clientes'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    razon_social = db.Column(db.String(150), nullable=True)
    cuit = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    telefono = db.Column(db.String(50), nullable=True)
    direccion = db.Column(db.String(200), nullable=True)
    creado_en = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    estado_id = db.Column(db.Integer, db.ForeignKey('status.id'), nullable=False)

    estado = db.relationship('Status', lazy=True)
    ventas = db.relationship('Venta', back_populates='cliente', lazy=True)
    personas_autorizadas = db.relationship('PersonaAutorizada', back_populates='cliente', lazy=True)

    def serialize(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "razon_social": self.razon_social,
            "cuit": self.cuit,
            "email": self.email,
            "telefono": self.telefono,
            "direccion": self.direccion,
            "creado_en": self.creado_en.isoformat(),
            "estado": self.estado.label if self.estado else None,
            "personas_autorizadas": [p.serialize() for p in self.personas_autorizadas]
        }
