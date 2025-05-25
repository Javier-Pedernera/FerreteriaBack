from datetime import datetime, timezone
from app.models.pedido_proveedor import PedidoProveedor
from app.models.detalle_pedido_proveedor import DetallePedidoProveedor
from app import db
from app.models.status import Status

class PedidoService:

    @staticmethod
    def get_all_pedidos():
        pedidos = PedidoProveedor.query.order_by(PedidoProveedor.fecha_pedido.desc()).all()
        return [pedido.serialize() for pedido in pedidos]

    @staticmethod
    def get_pedido_by_id(pedido_id):
        return PedidoProveedor.query.get(pedido_id)

    @staticmethod
    def crear_pedido(data):
        estado_pending = Status.query.filter_by(code="pending").first()
        if not estado_pending:
            raise ValueError("No se encontró el estado 'pending'")

        pedido = PedidoProveedor(
            proveedor_id=data["proveedor_id"],
            descuento=data.get("descuento", 0),
            estado_id=estado_pending.id
        )
        db.session.add(pedido)
        db.session.flush()

        for item in data["detalles"]:
            detalle = DetallePedidoProveedor(
                pedido_id=pedido.id,
                producto_id=item["producto_id"],
                cantidad=item["cantidad"],
                precio_unitario=item["precio_unitario"]
            )
            db.session.add(detalle)

        db.session.commit()
        return pedido.serialize()
    
    @staticmethod
    def actualizar_estado_pedido(pedido_id, nuevo_estado_id, numero_factura=None):
        pedido = PedidoProveedor.query.get(pedido_id)
        if not pedido:
            return None

        estado = Status.query.get(nuevo_estado_id)
        if not estado:
            raise ValueError("Estado no válido")
        if estado.code == 'paid' and pedido.estado.code != 'paid':
            pedido.fecha_pago = datetime.now(timezone.utc)
        
        if estado.code == 'received' and pedido.estado.code != 'received':
            pedido.fecha_llegada = datetime.now(timezone.utc)
            print("Ejecutando actualizar_stock() para pedido:", pedido.id)
            pedido.actualizar_stock()
            
        pedido.estado_id = nuevo_estado_id
        pedido.estado = estado
        if numero_factura:
            pedido.numero_factura = numero_factura

        db.session.commit()


        return pedido.serialize()

    @staticmethod
    def delete_pedido(pedido_id):
        pedido = PedidoProveedor.query.get(pedido_id)
        if pedido:
            db.session.delete(pedido)
            db.session.commit()
        return pedido
