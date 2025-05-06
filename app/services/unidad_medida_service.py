from app.models.unidad_medida import UnidadMedida
from app import db

class UnidadMedidaService:

    @staticmethod
    def obtener_todas():
        return UnidadMedida.query.order_by(UnidadMedida.nombre).all()

    @staticmethod
    def obtener_por_id(unidad_id):
        return UnidadMedida.query.get(unidad_id)

    @staticmethod
    def crear(data):
        nueva_unidad = UnidadMedida(
            nombre=data.get('nombre'),
            codigo=data.get('codigo'),
            icono=data.get('icono'),
            descripcion=data.get('descripcion')
        )
        db.session.add(nueva_unidad)
        db.session.commit()
        return nueva_unidad

    @staticmethod
    def actualizar(unidad_id, data):
        unidad = UnidadMedida.query.get(unidad_id)
        if unidad:
            unidad.nombre = data.get('nombre', unidad.nombre)
            unidad.codigo = data.get('codigo', unidad.codigo)
            unidad.icono = data.get('icono', unidad.icono)
            unidad.descripcion = data.get('descripcion', unidad.descripcion)
            db.session.commit()
        return unidad

    @staticmethod
    def eliminar(unidad_id):
        unidad = UnidadMedida.query.get(unidad_id)
        if unidad:
            db.session.delete(unidad)
            db.session.commit()
            return True
        return False
