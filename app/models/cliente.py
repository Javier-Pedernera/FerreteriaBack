from datetime import datetime, timezone
from decimal import Decimal
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
    cuenta_corriente_activa = db.Column(db.Boolean, default=False)
    saldo_favor = db.Column(db.Numeric(12,2), default=Decimal(0))
    
    tipo_documento_id = db.Column(
    db.Integer,
    db.ForeignKey("tipos_documento.id"),
    nullable=True
    )

    tipo_documento = db.relationship(
        "TipoDocumento",
        back_populates="clientes"
    )
    condicion_iva_id = db.Column(
        db.Integer,
        db.ForeignKey("condiciones_iva.id"),
        nullable=True
    )
    condicion_iva = db.relationship("CondicionIVA", lazy=True)
    estado = db.relationship('Status', lazy=True)
    ventas = db.relationship('Venta', back_populates='cliente', lazy=True)
    pagos = db.relationship('Pago', back_populates='cliente', lazy=True)
    personas_autorizadas = db.relationship('PersonaAutorizada', back_populates='cliente', lazy=True)

    def serialize(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "razon_social": self.razon_social,
            "cuit": self.cuit,
            "tipo_doc": self.tipo_documento.codigo_afip if self.tipo_documento else None,
            "tipo_doc_descripcion": self.tipo_documento.descripcion if self.tipo_documento else None,
            "email": self.email,
            "telefono": self.telefono,
            "direccion": self.direccion,
            "creado_en": self.creado_en.isoformat(),
            "estado": self.estado.label if self.estado else None,
            "personas_autorizadas": [p.serialize() for p in self.personas_autorizadas],
            "cuenta_corriente_activa": self.cuenta_corriente_activa,
            "saldo_favor": str(self.saldo_favor or 0),

            # ✅ NUEVO
            "condicion_iva": self.condicion_iva.codigo if self.condicion_iva else None
        }

