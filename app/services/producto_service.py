from app import db
from app.models.producto import Producto

class ProductoService:

    @staticmethod
    def obtener_todos():
        return Producto.query.all()

    @staticmethod
    def obtener_por_id(producto_id):
        return Producto.query.get_or_404(producto_id)

    @staticmethod
    def crear(data):
        producto = Producto(
            cod_interno=data['cod_interno'],
            cod_proveedor=data.get('cod_proveedor'),
            nombre=data['nombre'],
            descripcion=data.get('descripcion'),
            precio_ars=data['precio_ars'],
            precio_usd=data.get('precio_usd'),
            porcentaje_ganancia=data.get('porcentaje_ganancia'),
            disponibles=data.get('disponibles', 0),
            proveedor_id=data['proveedor_id'],
            categoria_id=data.get('categoria_id'),
            status_id=data['status_id'],
            unidad_medida_id=data['unidad_medida_id']
        )

        producto.precio_final = producto.calcular_precio_final()

        db.session.add(producto)
        db.session.commit()

        return producto

    @staticmethod
    def actualizar(producto_id, data):
        producto = Producto.query.get_or_404(producto_id)

        for campo in ['cod_interno', 'cod_proveedor', 'nombre', 'descripcion',
                      'precio_ars', 'precio_usd', 'porcentaje_ganancia', 'disponibles',
                      'proveedor_id', 'categoria_id', 'status_id', 'unidad_medida_id']:
            if campo in data:
                setattr(producto, campo, data[campo])

        producto.precio_final = producto.calcular_precio_final()
        db.session.commit()
        return producto

    @staticmethod
    def eliminar(producto_id):
        producto = Producto.query.get_or_404(producto_id)
        db.session.delete(producto)
        db.session.commit()
        return True