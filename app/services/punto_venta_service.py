from app import db
from app.models.punto_venta import PuntoVenta
from app.models.empresa_fiscal_config import EmpresaFiscalConfig


class PuntoVentaService:

    @staticmethod
    def crear_punto_venta(data):

        empresa_id = data.get("empresa_config_id")
        numero = data.get("numero")
        nombre = data.get("nombre")
        direccion = data.get("direccion")
        telefono = data.get("telefono")
        email = data.get("email")
        descripcion = data.get("descripcion")

        if not empresa_id:
            raise ValueError("empresa_config_id es obligatorio")

        if not numero:
            raise ValueError("numero de punto de venta es obligatorio")

        if not nombre:
            raise ValueError("nombre del punto de venta es obligatorio")

        empresa = EmpresaFiscalConfig.query.get(empresa_id)

        if not empresa:
            raise ValueError("Empresa fiscal no encontrada")

        existente = PuntoVenta.query.filter_by(
            empresa_config_id=empresa_id,
            numero=numero
        ).first()

        if existente:
            raise ValueError("Ese punto de venta ya existe para la empresa")

        pv = PuntoVenta(
            empresa_config_id=empresa_id,
            numero=numero,
            nombre=nombre,
            direccion=direccion,
            telefono=telefono,
            email=email,
            descripcion=descripcion
        )

        db.session.add(pv)
        db.session.commit()

        return pv


    @staticmethod
    def obtener_puntos_empresa(empresa_id):

        empresa = EmpresaFiscalConfig.query.get(empresa_id)

        if not empresa:
            raise ValueError("Empresa fiscal no encontrada")

        puntos = PuntoVenta.query.filter_by(
            empresa_config_id=empresa_id
        ).all()

        return puntos


    @staticmethod
    def obtener_punto(pv_id):

        pv = PuntoVenta.query.get(pv_id)

        if not pv:
            raise ValueError("Punto de venta no encontrado")

        return pv


    @staticmethod
    def actualizar_punto_venta(pv_id, data):

        pv = PuntoVenta.query.get(pv_id)

        if not pv:
            raise ValueError("Punto de venta no encontrado")

        pv.numero = data.get("numero", pv.numero)
        pv.nombre = data.get("nombre", pv.nombre)
        pv.direccion = data.get("direccion", pv.direccion)
        pv.telefono = data.get("telefono", pv.telefono)
        pv.email = data.get("email", pv.email)
        pv.descripcion = data.get("descripcion", pv.descripcion)

        db.session.commit()

        return pv


    @staticmethod
    def eliminar_punto_venta(pv_id):

        pv = PuntoVenta.query.get(pv_id)

        if not pv:
            raise ValueError("Punto de venta no encontrado")

        db.session.delete(pv)
        db.session.commit()

        return True