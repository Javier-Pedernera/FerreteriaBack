from app.models.proveedor import Proveedor
from app import db
from app.models.status import Status
from sqlalchemy import text

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

            # 🔁 Guardar primero el cambio del proveedor
            db.session.commit()

            # 🔁 Si cambió el porcentaje, hacé el update masivo
            if proveedor.porcentaje_ganancia != porcentaje_anterior:
                sql = text("""
                    UPDATE productos
                    SET 
                        porcentaje_ganancia = :porcentaje,
                        precio_final = ROUND(precio_ars * (1 + :porcentaje / 100), 2)
                    WHERE 
                        proveedor_id = :proveedor_id
                        AND (porcentaje_ganancia_personalizado = false OR porcentaje_ganancia_personalizado IS NULL)
                """)
                db.session.execute(sql, {
                    'porcentaje': proveedor.porcentaje_ganancia,
                    'proveedor_id': proveedor.id
                })

                # 🔁 Confirmar el update masivo
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
