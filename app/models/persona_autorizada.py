from app import db

class PersonaAutorizada(db.Model):
    __tablename__ = 'personas_autorizadas'

    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    dni = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    telefono = db.Column(db.String(50), nullable=True)
    estado_id = db.Column(db.Integer, db.ForeignKey('status.id'), nullable=False)

    cliente = db.relationship('Cliente', back_populates='personas_autorizadas', lazy=True)
    estado = db.relationship('Status', lazy=True)

    def serialize(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "apellido": self.apellido,
            "dni": self.dni,
            "email": self.email,
            "telefono": self.telefono,
            "estado": self.estado.label if self.estado else None
        }
