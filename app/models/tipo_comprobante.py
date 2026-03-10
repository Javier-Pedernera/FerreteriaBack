from app import db


class TipoComprobante(db.Model):
    __tablename__ = "tipos_comprobante"

    id = db.Column(db.Integer, primary_key=True)

    codigo_afip = db.Column(db.Integer, nullable=False, unique=True)
    descripcion = db.Column(db.String(100), nullable=False)

    # 🔹 NUEVA COLUMNA
    letra = db.Column(db.String(1), nullable=True)

    activo = db.Column(db.Boolean, default=True)

    def serialize(self):
        return {
            "id": self.id,
            "codigo_afip": self.codigo_afip,
            "descripcion": self.descripcion,
            "letra": self.letra,
            "activo": self.activo
        }