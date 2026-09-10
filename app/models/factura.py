from datetime import datetime, timezone
from app import db


class Factura(db.Model):
    __tablename__ = "facturas"

    id = db.Column(db.Integer, primary_key=True)

    cliente_id = db.Column(
        db.Integer,
        db.ForeignKey("clientes.id"),
        nullable=True
    )

    # Receptor cuando NO hay cliente registrado (venta de mostrador /
    # consumidor final). Si cliente_id está seteado, se ignoran estos campos
    # y los datos salen del Cliente. Guardan códigos AFIP directamente:
    #   receptor_doc_tipo: 99 = consumidor final, 96 = DNI, 80 = CUIT...
    #   receptor_condicion_iva: código de FEParamGetCondicionIvaReceptor
    #                           (5 = Consumidor Final)
    receptor_nombre = db.Column(db.String(150))
    receptor_doc_tipo = db.Column(db.Integer)
    receptor_doc_nro = db.Column(db.String(20))
    receptor_condicion_iva = db.Column(db.Integer)

    # 🔹 NUEVO — tipo profesional de comprobante
    tipo_comprobante_id = db.Column(
        db.Integer,
        db.ForeignKey("tipos_comprobante.id"),
        nullable=True
    )

    tipo_comprobante = db.relationship("TipoComprobante")

    fecha_creacion = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    # 🔹 NUEVO — fecha fiscal real del comprobante
    fecha_emision = db.Column(db.Date)

    total = db.Column(db.Numeric(14, 2), nullable=False)
    moneda = db.Column(db.String(10), default="ARS")

    # -------- CAMPOS ARCA --------
    arca_tipo_cbte = db.Column(db.Integer)
    
    punto_venta_emitido = db.Column(db.Integer)
    numero_comprobante = db.Column(db.String(20))
    
    punto_venta_id = db.Column(
        db.Integer,
        db.ForeignKey("puntos_venta.id"),
        nullable=True
    )

    punto_venta = db.relationship("PuntoVenta")

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

    cliente = db.relationship(
        "Cliente",
        backref="facturas",
        lazy=True
    )

    ventas = db.relationship("Venta", back_populates="factura")

    items = db.relationship(
        "FacturaItem",
        back_populates="factura",
        cascade="all, delete-orphan",
        lazy=True
    )

    # -------------------------
    # SERIALIZE
    # -------------------------

    def receptor_display(self):
        """Nombre a mostrar del receptor: cliente registrado, dato suelto, o Consumidor Final."""
        if self.cliente:
            return self.cliente.nombre
        return self.receptor_nombre or "Consumidor Final"

    def serialize(self):
        return {
            "id": self.id,
            "cliente_id": self.cliente_id,
            "receptor_nombre": self.receptor_nombre,
            "receptor_doc_tipo": self.receptor_doc_tipo,
            "receptor_doc_nro": self.receptor_doc_nro,
            "receptor_condicion_iva": self.receptor_condicion_iva,
            "receptor": self.receptor_display(),
            "fecha": self.fecha_creacion.isoformat(),
            "fecha_emision": self.fecha_emision.isoformat() if self.fecha_emision else None,
            "total": float(self.total),
            "moneda": self.moneda,
            "estado": self.estado,
            "numero": self.arca_numero_cbte,
            "numero_comprobante": self.numero_comprobante,
            "punto_venta_id": self.punto_venta_id,
            "puntoVenta": self.punto_venta_emitido if self.punto_venta_emitido else (
                self.punto_venta.numero if self.punto_venta else None
            ),
            "tipo": self.tipo_comprobante.codigo_afip if self.tipo_comprobante else self.arca_tipo_cbte,
            "cae": self.arca_cae,
            "items": [i.serialize() for i in self.items]
        }