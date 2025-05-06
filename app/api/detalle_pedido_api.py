from flask import Blueprint, request, jsonify
from app.services.detalle_pedido_service import DetallePedidoService

detalle_pedido_api = Blueprint('detalle_pedido_api', __name__)

@detalle_pedido_api.route('/detalles', methods=['GET'])
def get_all_detalles():
    detalles = DetallePedidoService.get_all_detalles()
    return jsonify([d.serialize() for d in detalles])

@detalle_pedido_api.route('/detalles/<int:detalle_id>', methods=['GET'])
def get_detalle_by_id(detalle_id):
    detalle = DetallePedidoService.get_detalle_by_id(detalle_id)
    if detalle:
        return jsonify(detalle.serialize())
    return jsonify({'error': 'Detalle no encontrado'}), 404

@detalle_pedido_api.route('/detalles/pedido/<int:pedido_id>', methods=['GET'])
def get_detalles_by_pedido(pedido_id):
    detalles = DetallePedidoService.get_detalles_by_pedido_id(pedido_id)
    return jsonify([d.serialize() for d in detalles])

@detalle_pedido_api.route('/detalles', methods=['POST'])
def create_detalle():
    data = request.json
    nuevo = DetallePedidoService.create_detalle(data)
    return jsonify(nuevo.serialize()), 201

@detalle_pedido_api.route('/detalles/<int:detalle_id>', methods=['PUT'])
def update_detalle(detalle_id):
    data = request.json
    actualizado = DetallePedidoService.update_detalle(detalle_id, data)
    if actualizado:
        return jsonify(actualizado.serialize())
    return jsonify({'error': 'Detalle no encontrado'}), 404

@detalle_pedido_api.route('/detalles/<int:detalle_id>', methods=['DELETE'])
def delete_detalle(detalle_id):
    eliminado = DetallePedidoService.delete_detalle(detalle_id)
    if eliminado:
        return jsonify({'message': 'Detalle eliminado'})
    return jsonify({'error': 'Detalle no encontrado'}), 404