from flask import Blueprint, request, jsonify
from app.services.pago_service import PagoService

pago_api = Blueprint('pago_api', __name__)

@pago_api.route('/', methods=['GET'])
def listar_pagos():
    cliente_id = request.args.get('cliente_id')
    pagos = PagoService.get_all_pagos(cliente_id)
    return jsonify([p.serialize() for p in pagos]), 200

@pago_api.route('/<int:pago_id>', methods=['GET'])
def obtener_pago(pago_id):
    pago = PagoService.get_pago_by_id(pago_id)
    if not pago:
        return jsonify({'error': 'Pago no encontrado'}), 404
    return jsonify(pago.serialize()), 200

@pago_api.route('/', methods=['POST'])
def crear_pago():
    data = request.json
    pago = PagoService.create_pago(data)
    return jsonify(pago.serialize()), 201

@pago_api.route('/<int:pago_id>', methods=['PUT'])
def actualizar_pago(pago_id):
    data = request.json
    pago = PagoService.update_pago(pago_id, data)
    if not pago:
        return jsonify({'error': 'Pago no encontrado'}), 404
    return jsonify(pago.serialize()), 200

@pago_api.route('/<int:pago_id>', methods=['DELETE'])
def eliminar_pago(pago_id):
    pago = PagoService.delete_pago(pago_id)
    if not pago:
        return jsonify({'error': 'Pago no encontrado'}), 404
    return jsonify({'message': 'Pago eliminado'}), 200