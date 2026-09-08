from datetime import datetime, timezone
from app import db

# Validado a nivel de aplicación (PresupuestoService), no como ENUM nativo de
# Postgres, mismo criterio que Nota: agregar un estado nuevo no debe requerir
# una migración de ALTER TYPE.
ESTADOS_PRESUPUESTO = ('pendiente', 'aceptado', 'rechazado', 'vencido', 'convertido')


class Presupuesto(db.Model):
    __tablename__ = 'presupuestos'
    __table_args__ = (
        db.Index('ix_presupuestos_estado', 'estado'),
        db.Index('ix_presupuestos_cliente_nombre', 'cliente_nombre'),
        db.Index('ix_presupuestos_cliente_cuit', 'cliente_cuit'),
        db.Index('ix_presupuestos_cliente_telefono', 'cliente_telefono'),
    )

    id = db.Column(db.Integer, primary_key=True)

    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=True)
    # Copia de los datos del cliente al momento de crear/editar el presupuesto
    # (si hay cliente_id, se completan desde Cliente; si no, son datos sueltos
    # de un cliente ocasional). Así la búsqueda por nombre/cuit/telefono no
    # depende de si el cliente está cargado en el sistema o no.
    cliente_nombre = db.Column(db.String(150), nullable=True)
    cliente_cuit = db.Column(db.String(20), nullable=True)
    cliente_telefono = db.Column(db.String(50), nullable=True)

    observaciones = db.Column(db.Text, nullable=True)

    total = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    estado = db.Column(db.String(20), nullable=False, default='pendiente')

    venta_id = db.Column(db.Integer, db.ForeignKey('ventas.id'), nullable=True)

    usuario_creador_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)

    # Soft delete propio, independiente del campo "estado" de negocio de arriba.
    eliminado = db.Column(db.Boolean, nullable=False, default=False)

    fecha_creacion = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    fecha_actualizacion = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    cliente = db.relationship('Cliente', lazy=True)
    venta = db.relationship('Venta', lazy=True)
    usuario_creador = db.relationship('Usuario', lazy=True)
    detalles = db.relationship(
        'DetallePresupuesto',
        back_populates='presupuesto',
        lazy=True,
        cascade='all, delete-orphan',
        order_by='DetallePresupuesto.id'
    )

    def serialize(self):
        return {
            'id': self.id,
            'cliente_id': self.cliente_id,
            'cliente_nombre': self.cliente_nombre,
            'cliente_cuit': self.cliente_cuit,
            'cliente_telefono': self.cliente_telefono,
            'observaciones': self.observaciones,
            'total': float(self.total or 0),
            'estado': self.estado,
            'venta_id': self.venta_id,
            'usuario_creador_id': self.usuario_creador_id,
            'usuario_creador': self.usuario_creador.nombre if self.usuario_creador else None,
            'detalles': [d.serialize() for d in self.detalles],
            'fecha_creacion': self.fecha_creacion.isoformat(),
            'fecha_actualizacion': self.fecha_actualizacion.isoformat() if self.fecha_actualizacion else None,
        }

    def __repr__(self):
        return f'<Presupuesto {self.id} {self.estado}>'


class DetallePresupuesto(db.Model):
    __tablename__ = 'detalles_presupuesto'
    __table_args__ = (
        db.Index('ix_detalles_presupuesto_presupuesto_id', 'presupuesto_id'),
    )

    id = db.Column(db.Integer, primary_key=True)
    presupuesto_id = db.Column(db.Integer, db.ForeignKey('presupuestos.id'), nullable=False)

    # Nullable: un ítem "manual" (sin producto del catálogo) no tiene producto_id.
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=True)
    cod_interno = db.Column(db.String(50), nullable=True)
    descripcion = db.Column(db.String(300), nullable=False)
    cantidad = db.Column(db.Numeric(10, 3), nullable=False)
    precio_unitario = db.Column(db.Numeric(12, 2), nullable=False)

    presupuesto = db.relationship('Presupuesto', back_populates='detalles', lazy=True)
    producto = db.relationship('Producto', lazy=True)

    def serialize(self):
        return {
            'id': self.id,
            'producto_id': self.producto_id,
            'cod_interno': self.cod_interno,
            'descripcion': self.descripcion,
            'cantidad': float(self.cantidad),
            'precio_unitario': float(self.precio_unitario),
            'subtotal': float(self.cantidad * self.precio_unitario),
        }
