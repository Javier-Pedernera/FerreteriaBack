from decimal import Decimal

from app import db
from app.models.presupuesto import Presupuesto, DetallePresupuesto, ESTADOS_PRESUPUESTO
from app.models.cliente import Cliente


class PresupuestoService:

    @staticmethod
    def _completar_datos_cliente(presupuesto, data):
        """
        Si viene cliente_id, copia nombre/cuit/telefono desde el Cliente real
        (es la fuente autoritativa). Si no, usa los campos sueltos que mandó
        el frontend (cliente ocasional, sin cuenta en el sistema).
        """
        if 'cliente_id' in data:
            presupuesto.cliente_id = data['cliente_id']

        if presupuesto.cliente_id:
            cliente = Cliente.query.get(presupuesto.cliente_id)
            if not cliente:
                raise ValueError(f"No existe el cliente {presupuesto.cliente_id}")
            presupuesto.cliente_nombre = cliente.nombre
            presupuesto.cliente_cuit = cliente.cuit
            presupuesto.cliente_telefono = cliente.telefono
        else:
            if 'cliente_nombre' in data:
                presupuesto.cliente_nombre = data.get('cliente_nombre')
            if 'cliente_cuit' in data:
                presupuesto.cliente_cuit = data.get('cliente_cuit')
            if 'cliente_telefono' in data:
                presupuesto.cliente_telefono = data.get('cliente_telefono')

    @staticmethod
    def _construir_detalles(detalles_data):
        if not detalles_data:
            raise ValueError("Debe incluir al menos un ítem en 'detalles'")

        detalles = []
        total = Decimal("0")
        for item in detalles_data:
            if not item.get('descripcion'):
                raise ValueError("Cada ítem necesita 'descripcion'")

            cantidad = Decimal(str(item.get('cantidad', 0)))
            precio_unitario = Decimal(str(item.get('precio_unitario', 0)))
            if cantidad <= 0:
                raise ValueError(f"Cantidad inválida en el ítem '{item.get('descripcion')}'")

            detalle = DetallePresupuesto(
                producto_id=item.get('producto_id'),
                cod_interno=item.get('cod_interno'),
                descripcion=item['descripcion'],
                cantidad=cantidad,
                precio_unitario=precio_unitario,
            )
            detalles.append(detalle)
            total += cantidad * precio_unitario

        return detalles, total

    @staticmethod
    def get_all_presupuestos(filtros=None):
        filtros = filtros or {}
        query = Presupuesto.query.filter(Presupuesto.eliminado.is_(False))

        estado = filtros.get('estado')
        if estado:
            query = query.filter(Presupuesto.estado == estado)

        texto = filtros.get('query')
        if texto:
            like = f"%{texto}%"
            query = query.filter(
                db.or_(
                    Presupuesto.cliente_nombre.ilike(like),
                    Presupuesto.cliente_cuit.ilike(like),
                    Presupuesto.cliente_telefono.ilike(like),
                )
            )

        return query.order_by(Presupuesto.fecha_creacion.desc()).all()

    @staticmethod
    def get_presupuesto_by_id(presupuesto_id):
        presupuesto = Presupuesto.query.get(presupuesto_id)
        if presupuesto and presupuesto.eliminado:
            return None
        return presupuesto

    @staticmethod
    def create_presupuesto(data):
        if not data.get('usuario_creador_id'):
            raise ValueError("El campo 'usuario_creador_id' es obligatorio")

        detalles, total = PresupuestoService._construir_detalles(data.get('detalles'))

        presupuesto = Presupuesto(
            observaciones=data.get('observaciones'),
            usuario_creador_id=data['usuario_creador_id'],
            estado='pendiente',
            total=total,
        )
        PresupuestoService._completar_datos_cliente(presupuesto, data)
        presupuesto.detalles = detalles

        db.session.add(presupuesto)
        db.session.commit()
        return presupuesto

    @staticmethod
    def update_presupuesto(presupuesto_id, data):
        presupuesto = PresupuestoService.get_presupuesto_by_id(presupuesto_id)
        if not presupuesto:
            return None

        PresupuestoService._completar_datos_cliente(presupuesto, data)

        if 'observaciones' in data:
            presupuesto.observaciones = data.get('observaciones')

        if 'detalles' in data:
            detalles, total = PresupuestoService._construir_detalles(data['detalles'])
            presupuesto.detalles = detalles
            presupuesto.total = total

        db.session.commit()
        return presupuesto

    @staticmethod
    def cambiar_estado(presupuesto_id, estado):
        if estado not in ESTADOS_PRESUPUESTO:
            raise ValueError(f"estado inválido. Valores permitidos: {ESTADOS_PRESUPUESTO}")

        presupuesto = PresupuestoService.get_presupuesto_by_id(presupuesto_id)
        if not presupuesto:
            return None

        presupuesto.estado = estado
        db.session.commit()
        return presupuesto

    @staticmethod
    def convertir_en_venta(presupuesto_id, venta_id):
        if not venta_id:
            raise ValueError("El campo 'venta_id' es obligatorio")

        presupuesto = PresupuestoService.get_presupuesto_by_id(presupuesto_id)
        if not presupuesto:
            return None

        presupuesto.estado = 'convertido'
        presupuesto.venta_id = venta_id
        db.session.commit()
        return presupuesto

    @staticmethod
    def delete_presupuesto(presupuesto_id):
        """Soft delete: no se borra la fila, se marca eliminado=True."""
        presupuesto = PresupuestoService.get_presupuesto_by_id(presupuesto_id)
        if not presupuesto:
            return False

        presupuesto.eliminado = True
        db.session.commit()
        return True
