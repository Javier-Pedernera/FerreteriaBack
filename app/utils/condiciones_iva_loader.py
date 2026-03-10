from app.models.condicion_iva import CondicionIVA
from app import db
import os

def initialize_condiciones_iva():

    # Definimos los códigos de AFIP
    condiciones = [
        {"codigo": "RI", "descripcion": "Responsable Inscripto", "codigo_afip": 1},
        {"codigo": "MT", "descripcion": "Monotributo", "codigo_afip": 2},
        {"codigo": "EX", "descripcion": "Exento", "codigo_afip": 3},
        {"codigo": "CF", "descripcion": "Consumidor Final", "codigo_afip": 5},
        {"codigo": "NI", "descripcion": "No Inscripto", "codigo_afip": 6},
    ]

    for c in condiciones:
        # Buscamos por código
        existe = CondicionIVA.query.filter_by(codigo=c["codigo"]).first()
        if not existe:
            db.session.add(CondicionIVA(**c))

    db.session.commit()