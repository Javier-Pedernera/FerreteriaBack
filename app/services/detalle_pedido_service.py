from app.models.detalle_pedido_proveedor import DetallePedidoProveedor
from app import db

class DetallePedidoService:

    @staticmethod
    def get_all_detalles():
        return DetallePedidoProveedor.query.all()

    @staticmethod
    def get_detalle_by_id(detalle_id):
        return DetallePedidoProveedor.query.get(detalle_id)

    @staticmethod
    def get_detalles_by_pedido_id(pedido_id):
        return DetallePedidoProveedor.query.filter_by(pedido_id=pedido_id).all()

    @staticmethod
    def create_detalle(data):
        nuevo = DetallePedidoProveedor(
            pedido_id=data.get('pedido_id'),
            producto_id=data.get('producto_id'),
            cantidad=data.get('cantidad'),
            precio_unitario=data.get('precio_unitario')
        )
        db.session.add(nuevo)
        db.session.commit()
        return nuevo

    @staticmethod
    def update_detalle(detalle_id, data):
        detalle = DetallePedidoProveedor.query.get(detalle_id)
        if detalle:
            detalle.producto_id = data.get('producto_id', detalle.producto_id)
            detalle.cantidad = data.get('cantidad', detalle.cantidad)
            detalle.precio_unitario = data.get('precio_unitario', detalle.precio_unitario)
            db.session.commit()
        return detalle

    @staticmethod
    def delete_detalle(detalle_id):
        detalle = DetallePedidoProveedor.query.get(detalle_id)
        if detalle:
            db.session.delete(detalle)
            db.session.commit()
        return detalle


