from app.models.categoria import Categoria
from app import db

def initialize_categorias():
    categorias_default = [
        {'nombre': 'Herramientas manuales', 'descripcion': 'Martillos, destornilladores, llaves, etc.', 'icono': 'wrench', 'orden': 1},
        {'nombre': 'Herramientas eléctricas', 'descripcion': 'Taladros, amoladoras, sierras, etc.', 'icono': 'bolt', 'orden': 2},
        {'nombre': 'Pinturas y accesorios', 'descripcion': 'Pinturas, rodillos, pinceles.', 'icono': 'paint-brush', 'orden': 3},
        {'nombre': 'Tornillería y fijaciones', 'descripcion': 'Tornillos, tarugos, clavos.', 'icono': 'screwdriver', 'orden': 4},
        {'nombre': 'Electricidad', 'descripcion': 'Cables, enchufes, lámparas.', 'icono': 'plug', 'orden': 5},
        {'nombre': 'Agua', 'descripcion': 'Accesorios para instalación y mantenimiento de agua.', 'icono': 'faucet', 'orden': 6},
        {'nombre': 'Gas', 'descripcion': 'Tuberías, conexiones y materiales para gas.', 'icono': 'flame', 'orden': 7},
        {'nombre': 'Jardinería', 'descripcion': 'Palas, mangueras, tijeras.', 'icono': 'leaf', 'orden': 8},
        {'nombre': 'Construcción', 'descripcion': 'Cemento, mezclas, bloques.', 'icono': 'hammer', 'orden': 9},
        {'nombre': 'Adhesivos y selladores', 'descripcion': 'Siliconas, pegamentos.', 'icono': 'tape', 'orden': 10},
        {'nombre': 'Seguridad industrial', 'descripcion': 'Guantes, cascos, gafas.', 'icono': 'shield', 'orden': 11},
    ]

    for cat in categorias_default:
        if not Categoria.query.filter_by(nombre=cat['nombre']).first():
            nueva = Categoria(**cat)
            db.session.add(nueva)

    db.session.commit()