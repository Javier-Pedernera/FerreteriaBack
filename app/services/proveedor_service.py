from app.models.proveedor import Proveedor
from app import db
from app.models.status import Status

class ProveedorService:

    @staticmethod
    def create_proveedor(data):
        status = Status.query.filter_by(code='active').first()
        proveedor = Proveedor(
            nombre=data['nombre'],
            codigo_proveedor=data['codigo_proveedor'],
            sitio_web=data.get('sitio_web'),
            direccion=data.get('direccion'),  
            porcentaje_ganancia=data.get('porcentaje_ganancia', 0),
            precio_con_iva=data.get('precio_con_iva', True),
            descripcion=data.get('descripcion'),
            status_id=status.id if status else None
        )
        db.session.add(proveedor)
        db.session.commit()
        return proveedor

    @staticmethod
    def update_proveedor(id, data):
        proveedor = Proveedor.query.get(id)
        if proveedor:
            porcentaje_anterior = proveedor.porcentaje_ganancia
            proveedor.nombre = data.get('nombre', proveedor.nombre)
            proveedor.codigo_proveedor = data.get('codigo_proveedor', proveedor.codigo_proveedor)
            proveedor.sitio_web = data.get('sitio_web', proveedor.sitio_web)
            proveedor.direccion = data.get('direccion', proveedor.direccion) 
            proveedor.porcentaje_ganancia = data.get('porcentaje_ganancia', proveedor.porcentaje_ganancia)
            proveedor.precio_con_iva = data.get('precio_con_iva', proveedor.precio_con_iva)
            proveedor.descripcion = data.get('descripcion', proveedor.descripcion)
            proveedor.status_id = data.get('status_id', proveedor.status_id)
            
            if proveedor.porcentaje_ganancia != porcentaje_anterior:
                for producto in proveedor.productos: 
                    if not producto.porcentaje_ganancia_personalizado:
                        producto.porcentaje_ganancia = proveedor.porcentaje_ganancia
                        producto.precio_final = producto.calcular_precio_final()
                    
            db.session.commit()
            return proveedor
        return None

    @staticmethod
    def get_proveedor(id):
        return Proveedor.query.get(id)

    @staticmethod
    def get_all_proveedores():
        return Proveedor.query.all()

    @staticmethod
    def delete_proveedor(id):
        proveedor = Proveedor.query.get(id)
        if proveedor:
            db.session.delete(proveedor)
            db.session.commit()
            return True
        return False
