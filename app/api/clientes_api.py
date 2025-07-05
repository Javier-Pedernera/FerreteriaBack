from flask import Blueprint, jsonify, request
from app import db
from app.services.cliente_service import ClienteService

clientes_bp = Blueprint('clientes_api', __name__)

@clientes_bp.route('/', methods=['GET'])
def listar_clientes():
    clientes = ClienteService.get_all_clientes()
    return jsonify([c.serialize() for c in clientes]), 200

@clientes_bp.route('/<int:cliente_id>', methods=['GET'])
def obtener_cliente(cliente_id):
    cliente = ClienteService.get_cliente_by_id(cliente_id)
    if not cliente:
        return jsonify({'error': 'Cliente no encontrado'}), 404
    return jsonify(cliente.serialize()), 200

@clientes_bp.route('/', methods=['POST'])
def crear_cliente():
    data = request.json
    cliente = ClienteService.create_cliente(data)
    return jsonify(cliente.serialize()), 201

@clientes_bp.route('/<int:cliente_id>', methods=['PUT'])
def actualizar_cliente(cliente_id):
    data = request.json
    cliente = ClienteService.update_cliente(cliente_id, data)
    if not cliente:
        return jsonify({'error': 'Cliente no encontrado'}), 404
    return jsonify(cliente.serialize()), 200