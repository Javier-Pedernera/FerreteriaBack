from datetime import datetime, timezone
from .. import db

class Cuenta(db.Model):
    __tablename__ = "cuentas"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    saldo = db.Column(db.Float, default=0, nullable=False)
    moneda = db.Column(db.String(10), default="ARS")
    fecha_creacion = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    titular = db.Column(db.String(150), nullable=False)
    cbu = db.Column(db.String(30), nullable=True, unique=True)
    alias = db.Column(db.String(30), nullable=True, unique=True)

    status_id = db.Column(db.Integer, db.ForeignKey("status.id"), nullable=False)
    status = db.relationship("Status", backref="cuentas")

    movimientos = db.relationship(
    "MovimientoCuenta",
    back_populates="cuenta",
    lazy=True,
    foreign_keys="MovimientoCuenta.cuenta_id"
)

    def __repr__(self):
        return f"<Cuenta {self.nombre} {self.moneda}>"

    def serialize(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "saldo": self.saldo,
            "moneda": self.moneda,
            "titular": self.titular,
            "cbu": self.cbu,
            "alias": self.alias,
            "fecha_creacion": self.fecha_creacion.isoformat(),
            "status": self.status.serialize() if self.status else None
        }