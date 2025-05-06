from app import db

class UnidadMedida(db.Model):
    __tablename__ = 'unidades_medida'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)
    codigo = db.Column(db.String(10), unique=True, nullable=False)
    icono = db.Column(db.String(100), nullable=True)
    descripcion = db.Column(db.String(100), nullable=True)

    productos = db.relationship('Producto', back_populates='unidad_medida', lazy=True)

    def serialize(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'codigo': self.codigo,
            'icono': self.icono,
            'descripcion': self.descripcion
        }

    def __repr__(self):
        return f'<UnidadMedida {self.codigo} - {self.nombre}>'