from app.models.condicion_iva import CondicionIVA
from app import db


def initialize_condiciones_iva():

    condiciones = [
        {"codigo": "RI", "descripcion": "Responsable Inscripto"},
        {"codigo": "MT", "descripcion": "Monotributo"},
        {"codigo": "EX", "descripcion": "Exento"},
        {"codigo": "CF", "descripcion": "Consumidor Final"},
        {"codigo": "NI", "descripcion": "No Inscripto"},
    ]

    for c in condiciones:
        existe = CondicionIVA.query.filter_by(codigo=c["codigo"]).first()
        if not existe:
            db.session.add(CondicionIVA(**c))

    db.session.commit()