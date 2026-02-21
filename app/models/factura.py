from datetime import datetime, timezone
from app import db

class Factura(db.Model):
    __tablename__ = "facturas"

    id = db.Column(db.Integer, primary_key=True)

    cliente_id = db.Column(
        db.Integer,
        db.ForeignKey("clientes.id"),
        nullable=False
    )

    fecha_creacion = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    total = db.Column(db.Numeric(14, 2), nullable=False)
    moneda = db.Column(db.String(10), default="ARS")

    # -------- CAMPOS ARCA --------
    arca_tipo_cbte = db.Column(db.Integer)
    arca_punto_venta = db.Column(db.Integer)
    arca_numero_cbte = db.Column(db.Integer)

    arca_cae = db.Column(db.String(20))
    arca_cae_vto = db.Column(db.Date)

    arca_resultado = db.Column(db.String(20))
    arca_obs = db.Column(db.Text)

    estado = db.Column(db.String(20), default="pendiente")
    # pendiente | emitida | error

    # -------------------------
    # RELACIONES
    # -------------------------

    ventas = db.relationship("Venta", back_populates="factura")

    # ✅ NUEVO — items de factura (fiscal)
    items = db.relationship(
        "FacturaItem",
        back_populates="factura",
        cascade="all, delete-orphan",
        lazy=True
    )

    # -------------------------
    # SERIALIZE
    # -------------------------

    def serialize(self):
        return {
            "id": self.id,
            "cliente_id": self.cliente_id,
            "fecha": self.fecha_creacion.isoformat(),
            "total": float(self.total),
            "estado": self.estado,
            "numero": self.arca_numero_cbte,
            "puntoVenta": self.arca_punto_venta,
            "tipo": self.arca_tipo_cbte,
            "cae": self.arca_cae,

            # ✅ opcional pero recomendable
            "items": [i.serialize() for i in self.items]
        }