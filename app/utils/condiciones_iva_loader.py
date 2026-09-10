from app.models.condicion_iva import CondicionIVA
from app import db
import os

def initialize_condiciones_iva():

    # Códigos oficiales de AFIP para "Condición IVA del receptor"
    # (confirmados llamando a FEParamGetCondicionIvaReceptor en producción).
    # "NI" no tiene un equivalente exacto en esta tabla; se usa el más
    # cercano ("Sujeto No Categorizado").
    condiciones = [
        {"codigo": "RI", "descripcion": "Responsable Inscripto", "codigo_afip": 1},
        {"codigo": "MT", "descripcion": "Monotributo", "codigo_afip": 6},
        {"codigo": "EX", "descripcion": "Exento", "codigo_afip": 4},
        {"codigo": "CF", "descripcion": "Consumidor Final", "codigo_afip": 5},
        {"codigo": "NI", "descripcion": "No Inscripto", "codigo_afip": 7},
    ]

    for c in condiciones:
        # Buscamos por código
        existe = CondicionIVA.query.filter_by(codigo=c["codigo"]).first()
        if not existe:
            db.session.add(CondicionIVA(**c))
        elif existe.codigo_afip != c["codigo_afip"]:
            # backfill: filas creadas antes de que existiera codigo_afip
            existe.codigo_afip = c["codigo_afip"]

    db.session.commit()