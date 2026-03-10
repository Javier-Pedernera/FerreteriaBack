from app import db
from app.models.tipo_comprobante import TipoComprobante


def initialize_tipos_comprobante():
    tipos_default = [
        {"codigo_afip": 1, "descripcion": "Factura A", "letra": "A"},
        {"codigo_afip": 2, "descripcion": "Nota de Débito A", "letra": "A"},
        {"codigo_afip": 3, "descripcion": "Nota de Crédito A", "letra": "A"},
        {"codigo_afip": 6, "descripcion": "Factura B", "letra": "B"},
        {"codigo_afip": 7, "descripcion": "Nota de Débito B", "letra": "B"},
        {"codigo_afip": 8, "descripcion": "Nota de Crédito B", "letra": "B"},
        {"codigo_afip": 11, "descripcion": "Factura C", "letra": "C"},
        {"codigo_afip": 12, "descripcion": "Nota de Débito C", "letra": "C"},
        {"codigo_afip": 13, "descripcion": "Nota de Crédito C", "letra": "C"},
        {"codigo_afip": 51, "descripcion": "Factura M", "letra": "M"},
    ]

    for tipo_data in tipos_default:
        existe = TipoComprobante.query.filter_by(
            codigo_afip=tipo_data["codigo_afip"]
        ).first()

        if not existe:
            nuevo = TipoComprobante(**tipo_data)
            db.session.add(nuevo)

    db.session.commit()