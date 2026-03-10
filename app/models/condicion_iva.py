from app import db

class CondicionIVA(db.Model):
    __tablename__ = "condiciones_iva"

    id = db.Column(db.Integer, primary_key=True)

    codigo = db.Column(db.String(30), unique=True, nullable=False)
    descripcion = db.Column(db.String(100), nullable=False)
    codigo_afip = db.Column(db.Integer, nullable=True) 
    
    def serialize(self):
        return {
            "id": self.id,
            "codigo": self.codigo,
            "descripcion": self.descripcion,
            "codigo_afip": self.codigo_afip
        }