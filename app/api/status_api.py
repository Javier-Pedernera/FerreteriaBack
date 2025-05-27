from flask import Blueprint, request, jsonify
from app.services.status_service import StatusService

status_api = Blueprint('status_api', __name__)

@status_api.route('/status', methods=['GET'])
def listar_status():
    estados = StatusService.get_all_status()
    return jsonify([e.serialize() for e in estados]), 200

@status_api.route('/status/<int:status_id>', methods=['GET'])
def obtener_status(status_id):
    estado = StatusService.get_status_by_id(status_id)
    if not estado:
        return jsonify({'error': 'Estado no encontrado'}), 404
    return jsonify(estado.serialize()), 200

@status_api.route('/status', methods=['POST'])
def crear_status():
    data = request.json
    estado = StatusService.create_status(data)
    return jsonify(estado.serialize()), 201

@status_api.route('/status/<int:status_id>', methods=['PUT'])
def actualizar_status(status_id):
    data = request.json
    estado = StatusService.update_status(status_id, data)
    if not estado:
        return jsonify({'error': 'Estado no encontrado'}), 404
    return jsonify(estado.serialize()), 200

@status_api.route('/status/<int:status_id>', methods=['DELETE'])
def eliminar_status(status_id):
    estado = StatusService.delete_status(status_id)
    if not estado:
        return jsonify({'error': 'Estado no encontrado'}), 404
    return jsonify({'message': 'Estado eliminado'}), 200

