from app import db


class TipoDocumento(db.Model):
    __tablename__ = "tipos_documento"

    id = db.Column(db.Integer, primary_key=True)

    # Código oficial AFIP
    codigo_afip = db.Column(db.Integer, nullable=False, unique=True)

    descripcion = db.Column(db.String(100), nullable=False)

    activo = db.Column(db.Boolean, default=True)

    # Relación inversa
    clientes = db.relationship("Cliente", back_populates="tipo_documento")

    def serialize(self):
        return {
            "id": self.id,
            "codigo_afip": self.codigo_afip,
            "descripcion": self.descripcion,
        }