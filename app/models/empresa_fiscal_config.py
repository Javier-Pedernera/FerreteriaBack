from app import db

class EmpresaFiscalConfig(db.Model):
    __tablename__ = "empresa_fiscal_config"

    id = db.Column(db.Integer, primary_key=True)

    razon_social = db.Column(db.String(150), nullable=False)
    cuit = db.Column(db.String(20), nullable=False, unique=True)

    puntos_venta = db.relationship(
        "PuntoVenta",
        backref="empresa_config",
        lazy=True,
        cascade="all, delete-orphan"
    )

    condicion_iva_id = db.Column(
        db.Integer,
        db.ForeignKey("condiciones_iva.id"),
        nullable=False
    )

    condicion_iva = db.relationship("CondicionIVA")

    cert_path = db.Column(db.String(255), nullable=False)

    # 🔴 ESTA ES LA NUEVA COLUMNA
    pfx_password = db.Column(db.String(255), nullable=True)

    ambiente = db.Column(db.String(20), default="testing")

    activo = db.Column(db.Boolean, default=True)

    def serialize(self):
        return {
            "id": self.id,
            "razon_social": self.razon_social,
            "cuit": self.cuit,
            "puntos_venta": [pv.serialize() for pv in self.puntos_venta],
            "condicion_iva": self.condicion_iva.codigo if self.condicion_iva else None,
            "ambiente": self.ambiente,
            "activo": self.activo
        }