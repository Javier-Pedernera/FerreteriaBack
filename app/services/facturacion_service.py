from decimal import Decimal
from app import db
from app.models import Venta, Factura
from app.models.factura_item import FacturaItem
from app.services.arca_service import ArcaService
from app.models.status import Status

class FacturacionService:

    @staticmethod
    def crear_factura_desde_ventas(ventas_ids):

        deleted_status_id = db.session.query(Status.id)\
            .filter(Status.code == "deleted")\
            .scalar()

        ventas = (
            Venta.query
            .filter(Venta.id.in_(ventas_ids))
            .filter(Venta.estado_id != deleted_status_id)
            .all()
        )

        if not ventas:
            raise ValueError("No se encontraron ventas")

        # mismo cliente
        clientes = {v.cliente_id for v in ventas}
        if len(clientes) != 1:
            raise ValueError("Todas las ventas deben ser del mismo cliente")

        # no facturadas
        if any(v.factura_id for v in ventas):
            raise ValueError("Alguna venta ya está facturada")

        # facturables
        if any(not v.facturable for v in ventas):
            raise ValueError("Alguna venta no es facturable")

        # -------------------------
        # crear factura
        # -------------------------

        total = sum((v.total or 0) for v in ventas)

        factura = Factura(
            cliente_id=ventas[0].cliente_id,
            total=Decimal(total),
            estado="pendiente"
        )

        db.session.add(factura)
        db.session.flush()

        # -------------------------
        # crear items desde detalles
        # -------------------------

        for venta in ventas:
            for det in venta.detalles:

                subtotal = Decimal(det.cantidad) * Decimal(det.precio_unitario)

                item = FacturaItem(
                    factura_id=factura.id,
                    producto_id=det.producto_id,
                    descripcion=det.producto.nombre if det.producto else "Item",
                    cantidad=det.cantidad,
                    precio_unitario=det.precio_unitario,
                    subtotal=subtotal,
                    iva_porcentaje=21.0  # después lo hacemos dinámico
                )

                db.session.add(item)

            # vincular venta → factura
            venta.factura_id = factura.id

        db.session.commit()

        return factura
    
    @staticmethod
    def emitir_factura_arca(factura_id):

        factura = Factura.query.get(factura_id)
        if not factura:
            raise ValueError("Factura no encontrada")

        if factura.estado == "emitida":
            raise ValueError("Factura ya emitida")

        arca = ArcaService()

        resp = arca.emitir_comprobante(factura)

        factura.arca_numero_cbte = resp["numero"]
        factura.arca_cae = resp["cae"]
        factura.arca_cae_vto = resp["vto"]
        factura.arca_resultado = "A"
        factura.estado = "emitida"

        db.session.commit()

        return factura