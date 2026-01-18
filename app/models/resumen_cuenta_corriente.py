from datetime import datetime, timezone
from decimal import Decimal
from .. import db


class ResumenCuentaCorriente(db.Model):
    __tablename__ = 'resumenes_cuenta_corriente'

    id = db.Column(db.Integer, primary_key=True)

    cliente_id = db.Column(
        db.Integer,
        db.ForeignKey('clientes.id'),
        nullable=False,
        index=True
    )

    status_id = db.Column(
        db.Integer,
        db.ForeignKey('status.id'),
        nullable=False,
        index=True
    )

    fecha_desde = db.Column(
        db.DateTime(timezone=True),
        nullable=False
    )

    fecha_hasta = db.Column(
        db.DateTime(timezone=True),
        nullable=False
    )

    total = db.Column(
        db.Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00")
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    # relaciones
    cliente = db.relationship('Cliente', backref='resumenes_cuenta_corriente')
    status = db.relationship('Status')

    def __repr__(self):
        return f'<ResumenCuentaCorriente id={self.id} cliente={self.cliente_id}>'

    def serialize(self):
        return {
            'id': self.id,
            'cliente_id': self.cliente_id,
            'status': self.status.serialize() if self.status else None,
            'fecha_desde': self.fecha_desde.isoformat(),
            'fecha_hasta': self.fecha_hasta.isoformat(),
            'total': float(self.total),
            'created_at': self.created_at.isoformat()
        }