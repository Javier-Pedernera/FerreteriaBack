from datetime import datetime, timezone

from flask import jsonify
from app.models.pedido_proveedor import PedidoProveedor
from app.models.detalle_pedido_proveedor import DetallePedidoProveedor
from app import db
from app.models.status import Status

class PedidoService:

    @staticmethod
    def get_pedidos_paginados(page=1, limit=15, estado_code=None):
        query = PedidoProveedor.query

        if estado_code:
            estado = Status.query.filter_by(code=estado_code).first()
            if estado:
                query = query.filter_by(estado_id=estado.id)

        pagination = query.order_by(PedidoProveedor.fecha_pedido.desc()) \
                        .paginate(page=page, per_page=limit, error_out=False)

        return jsonify({
            "pedidos": [pedido.serialize() for pedido in pagination.items],
            "total": pagination.total,
            "pages": pagination.pages,
            "page": pagination.page
        })

    @staticmethod
    def get_pedido_by_id(pedido_id):
        pedido = PedidoProveedor.query.get(pedido_id)
        return pedido.serialize() if pedido else None

    @staticmethod
    def crear_pedido(data):
        estado_pending = Status.query.filter_by(code="pending").first()
        if not estado_pending:
            raise ValueError("No se encontró el estado 'pending'")

        # 🔒 Validar si ya hay un pedido pendiente o enviado para este proveedor
        pedido_existente = PedidoProveedor.query.filter(
            PedidoProveedor.proveedor_id == data["proveedor_id"],
            PedidoProveedor.estado.has(Status.code.in_(["pending"]))
        ).first()

        if pedido_existente:
            from flask import abort, jsonify
            return abort(400, description=jsonify({
                "error": "Ya existe un pedido en curso para este proveedor",
                "pedido_id": pedido_existente.id
            }))

        # 🟢 Crear pedido normalmente
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

    @staticmethod
    def obtener_pedido_pendiente_por_proveedor(proveedor_id):
        estado_pending = Status.query.filter_by(code="pending").first()
        if not estado_pending:
            raise ValueError("No se encontró el estado 'pending'")

        pedido = PedidoProveedor.query.filter_by(
            proveedor_id=proveedor_id,
            estado_id=estado_pending.id
        ).first()

        if pedido:
            return pedido.serialize()

        return None