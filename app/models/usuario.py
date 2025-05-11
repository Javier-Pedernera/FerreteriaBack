from datetime import datetime, timezone
from app import db
from werkzeug.security import generate_password_hash, check_password_hash

class Usuario(db.Model):
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=True)
    telefono = db.Column(db.String(50), nullable=True)
    creado_en = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    estado_id = db.Column(db.Integer, db.ForeignKey('status.id'), nullable=False)
    password_hash = db.Column(db.Text, nullable=False)

    
    ventas = db.relationship('Venta', back_populates='vendedor', lazy=True)
    estado = db.relationship('Status', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
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
