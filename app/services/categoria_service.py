from app.models.categoria import Categoria
from app import db

class CategoriaService:

    @staticmethod
    def get_all_categorias():
        return Categoria.query.order_by(Categoria.orden.asc()).all()

    @staticmethod
    def get_categoria_by_id(categoria_id):
        return Categoria.query.get(categoria_id)

    @staticmethod
    def create_categoria(data):
        nueva = Categoria(
            nombre=data.get('nombre'),
            descripcion=data.get('descripcion'),
            icono=data.get('icono'),
            orden=data.get('orden', 0)
        )
        db.session.add(nueva)
        db.session.commit()
        return nueva

    @staticmethod
    def update_categoria(categoria_id, data):
        categoria = Categoria.query.get(categoria_id)
        if categoria:
            categoria.nombre = data.get('nombre', categoria.nombre)
            categoria.descripcion = data.get('descripcion', categoria.descripcion)
            categoria.icono = data.get('icono', categoria.icono)
            categoria.orden = data.get('orden', categoria.orden)
            db.session.commit()
        return categoria

    @staticmethod
    def delete_categoria(categoria_id):
        categoria = Categoria.query.get(categoria_id)
        if categoria:
            db.session.delete(categoria)
            db.session.commit()
        return categoria
