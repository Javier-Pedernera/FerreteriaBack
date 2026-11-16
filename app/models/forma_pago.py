from app import db

class FormaPago(db.Model):
    __tablename__ = 'formas_pago'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text, nullable=True)
    activa = db.Column(db.Boolean, default=True, nullable=False)
    # URL de una imagen guardada en app/static/uploads/formas_pago/.
    icono = db.Column(db.String(255), nullable=True)

    ventas = db.relationship('Venta', back_populates='forma_pago', lazy=True)

    def serialize(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "descripcion": self.descripcion,
            "activa": self.activa,
            "icono": self.icono
        }