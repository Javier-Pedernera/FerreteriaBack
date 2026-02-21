from app import db

class EmpresaFiscalConfig(db.Model):
    __tablename__ = "empresa_fiscal_config"

    id = db.Column(db.Integer, primary_key=True)

    razon_social = db.Column(db.String(150), nullable=False)
    cuit = db.Column(db.String(20), nullable=False, unique=True)

    punto_venta = db.Column(db.Integer, nullable=False)

    condicion_iva_id = db.Column(
        db.Integer,
        db.ForeignKey("condiciones_iva.id"),
        nullable=False
    )
    # responsable_inscripto
    # monotributo
    # exento
    # etc

    cert_path = db.Column(db.String(255), nullable=True)
    key_path = db.Column(db.String(255), nullable=True)

    ambiente = db.Column(db.String(20), default="testing")
    # testing | produccion

    activo = db.Column(db.Boolean, default=True)

    def serialize(self):
        return {
            "id": self.id,
            "razon_social": self.razon_social,
            "cuit": self.cuit,
            "punto_venta": self.punto_venta,
            "condicion_iva": self.condicion_iva.codigo if self.condicion_iva else None,
            "ambiente": self.ambiente,
            "activo": self.activo
        }
