from app import db
from app.models.tipo_documento import TipoDocumento


def initialize_tipos_documento():
    tipos_default = [
        {"codigo_afip": 80, "descripcion": "CUIT"},
        {"codigo_afip": 86, "descripcion": "CUIL"},
        {"codigo_afip": 96, "descripcion": "DNI"},
        {"codigo_afip": 94, "descripcion": "Pasaporte"},
        {"codigo_afip": 99, "descripcion": "Consumidor Final"},
    ]

    for tipo_data in tipos_default:
        existe = TipoDocumento.query.filter_by(
            codigo_afip=tipo_data["codigo_afip"]
        ).first()

        if not existe:
            nuevo = TipoDocumento(**tipo_data)
            db.session.add(nuevo)

    db.session.commit()