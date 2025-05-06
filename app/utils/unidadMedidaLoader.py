from app.models.unidad_medida import UnidadMedida
from app import db

def initialize_unidades_medida():
    unidades_default = [
        {'nombre': 'Unidad', 'codigo': 'u', 'icono': 'square', 'descripcion': 'Unidad individual'},
        {'nombre': 'Metro', 'codigo': 'm', 'icono': 'ruler', 'descripcion': 'Medida de longitud'},
        {'nombre': 'Litro', 'codigo': 'l', 'icono': 'droplet', 'descripcion': 'Medida de volumen'},
        {'nombre': 'Kilogramo', 'codigo': 'kg', 'icono': 'weight', 'descripcion': 'Medida de peso'},
        {'nombre': 'Caja', 'codigo': 'caja', 'icono': 'box', 'descripcion': 'Presentación en caja'},
        {'nombre': 'Bolsa', 'codigo': 'bolsa', 'icono': 'shopping-bag', 'descripcion': 'Empaque tipo bolsa'},
        {'nombre': 'Par', 'codigo': 'par', 'icono': 'sliders', 'descripcion': 'Un par de unidades'},
        {'nombre': 'Juego', 'codigo': 'juego', 'icono': 'puzzle-piece', 'descripcion': 'Conjunto de piezas'},
    ]

    for unidad in unidades_default:
        if not UnidadMedida.query.filter_by(codigo=unidad['codigo']).first():
            nueva = UnidadMedida(**unidad)
            db.session.add(nueva)

    db.session.commit()