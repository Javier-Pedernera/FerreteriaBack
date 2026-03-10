from app import db

class PuntoVenta(db.Model):
    __tablename__ = "puntos_venta"

    id = db.Column(db.Integer, primary_key=True)

    empresa_config_id = db.Column(
        db.Integer,
        db.ForeignKey("empresa_fiscal_config.id"),
        nullable=False
    )

    numero = db.Column(db.Integer, nullable=False)

    nombre = db.Column(db.String(100), nullable=False)
    direccion = db.Column(db.String(200), nullable=True)
    telefono = db.Column(db.String(50), nullable=True)
    email = db.Column(db.String(50), nullable=True)
    descripcion = db.Column(db.String(100), nullable=True)

    activo = db.Column(db.Boolean, default=True)

    __table_args__ = (
        db.UniqueConstraint(
            "empresa_config_id",
            "numero",
            name="uq_empresa_punto_venta"
        ),
    )

    def serialize(self):
        return {
            "id": self.id,
            "numero": self.numero,
            "nombre": self.nombre,
            "direccion": self.direccion,
            "telefono": self.telefono,
            "email": self.email,
            "descripcion": self.descripcion,
            "activo": self.activo
        }