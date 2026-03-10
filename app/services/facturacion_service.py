from datetime import date
from decimal import Decimal
from app import db
from app.models import Venta, Factura
from app.models.factura_item import FacturaItem
from app.models.punto_venta import PuntoVenta
from app.models.tipo_comprobante import TipoComprobante
from app.services.arca_service import ArcaService
from app.models.status import Status
from app.services.empresa_fiscal_service import EmpresaFiscalService

class FacturacionService:

    @staticmethod
    def crear_factura_desde_ventas(cliente_id, ventas_ids,punto_venta_id, tipo_comprobante_id=None):
        """
        Crea una factura para un cliente unificando varias ventas.
        """
        punto_venta = PuntoVenta.query.get(punto_venta_id)

        if not punto_venta:
            raise ValueError("Punto de venta inválido")
        # obtener el status "deleted" para filtrar
        deleted_status_id = db.session.query(Status.id)\
            .filter(Status.code == "deleted")\
            .scalar()

        # traer ventas válidas
        ventas = (
            Venta.query
            .filter(Venta.id.in_(ventas_ids))
            .filter(Venta.cliente_id == cliente_id)  # filtramos por cliente
            .filter(Venta.estado_id != deleted_status_id)
            .all()
        )

        if not ventas:
            raise ValueError("No se encontraron ventas para ese cliente")

        # verificar que todas las ventas sean del mismo cliente (redundante pero seguro)
        clientes = {v.cliente_id for v in ventas}
        if len(clientes) != 1:
            raise ValueError("Todas las ventas deben ser del mismo cliente")

        # verificar que ninguna ya esté facturada
        if any(v.factura_id for v in ventas):
            raise ValueError("Alguna venta ya está facturada")

        # verificar que sean facturables
        if any(not getattr(v, "facturable", True) for v in ventas):
            raise ValueError("Alguna venta no es facturable")

        # -------------------------
        # crear factura
        # -------------------------
        total = sum((v.total or 0) for v in ventas)

        factura = Factura(
            cliente_id=cliente_id,
            total=Decimal(total),
            estado="pendiente",
            tipo_comprobante_id=tipo_comprobante_id,
            punto_venta_id=punto_venta_id
        )

        db.session.add(factura)
        db.session.flush()  # necesario para tener factura.id

        # -------------------------
        # crear items desde detalles de venta
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
                    iva_porcentaje=21.0  # después lo hacemos dinámico según cliente/producto
                )

                db.session.add(item)

            # vincular venta → factura
            venta.factura_id = factura.id

        db.session.commit()

        return factura
    
    @staticmethod
    def actualizar_factura(factura_id, data):
        factura = Factura.query.get(factura_id)

        if not factura:
            raise ValueError("Factura no encontrada")

        if factura.estado != "pendiente":
            raise ValueError("Solo se pueden modificar facturas pendientes")
        punto_venta_id = data.get("punto_venta_id")

        punto_venta_id = data.get("punto_venta_id")

        if punto_venta_id:
            factura.punto_venta_id = punto_venta_id
        # -------------------------
        # ACTUALIZAR TIPO
        # -------------------------
        tipo_comprobante_id = data.get("tipo_comprobante_id")

        if tipo_comprobante_id:
            tipo = TipoComprobante.query.get(tipo_comprobante_id)
            if not tipo:
                raise ValueError("Tipo de comprobante inválido")

            factura.tipo_comprobante_id = tipo.id

        # -------------------------
        # ACTUALIZAR ESTADO (opcional)
        # -------------------------
        nuevo_estado = data.get("estado")
        if nuevo_estado:
            factura.estado = nuevo_estado

        db.session.commit()

        return factura
    
    @staticmethod
    def emitir_factura_arca(factura_id):

        factura = Factura.query.get(factura_id)
        if not factura:
            raise ValueError("Factura no encontrada")

        if factura.estado == "emitida":
            raise ValueError("Factura ya emitida")

        # 🔴 VALIDACIÓN CLAVE
        if not factura.tipo_comprobante:
            raise ValueError("La factura no tiene tipo de comprobante asignado")

        if not factura.punto_venta:
            raise ValueError("La factura no tiene punto de venta asignado")

        empresa_config = EmpresaFiscalService.get_empresa_activa()
        if not empresa_config:
            raise ValueError("No hay empresa fiscal activa")

        arca = ArcaService(empresa_config)

        resp = arca.emitir_comprobante(factura)
        print("TIPO OBJ tipo_comprobante solo:", factura.tipo_comprobante)
        # 🔹 Guardamos el comprobante emitido
        factura.arca_tipo_cbte = factura.tipo_comprobante.codigo_afip
        factura.punto_venta_emitido = factura.punto_venta.numero
        factura.arca_numero_cbte = resp["numero"]

        # 🔹 NUEVO — número completo de comprobante
        factura.numero_comprobante = f"{factura.punto_venta_emitido:04d}-{factura.arca_numero_cbte:08d}"

        # 🔹 NUEVO — fecha fiscal de emisión
        factura.fecha_emision = date.today()

        factura.arca_cae = resp["cae"]
        factura.arca_cae_vto = resp["vto"]
        factura.arca_resultado = "A"
        factura.estado = "emitida"

        db.session.commit()

        return factura