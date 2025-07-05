from flask import Blueprint, request, jsonify
from app.services.personas_autorizadas_service import PersonaAutorizadaService

personas_api = Blueprint('personas_api', __name__)

@personas_api.route('/', methods=['GET'])
def listar_personas():
    personas = PersonaAutorizadaService.get_all()
    return jsonify([p.serialize() for p in personas]), 200

@personas_api.route('/<int:persona_id>', methods=['GET'])
def obtener_persona(persona_id):
    persona = PersonaAutorizadaService.get_by_id(persona_id)
    if not persona:
        return jsonify({'error': 'Persona autorizada no encontrada'}), 404
    return jsonify(persona.serialize()), 200

@personas_api.route('/', methods=['POST'])
def crear_persona():
    data = request.json
    try:
        persona = PersonaAutorizadaService.create(data)
        return jsonify(persona.serialize()), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@personas_api.route('/<int:persona_id>', methods=['PUT'])
def actualizar_persona(persona_id):
    data = request.json
    persona = PersonaAutorizadaService.update(persona_id, data)
    if not persona:
        return jsonify({'error': 'Persona autorizada no encontrada'}), 404
    return jsonify(persona.serialize()), 200

@personas_api.route('/<int:persona_id>/inactivar', methods=['PUT'])
def inactivar_persona(persona_id):
    try:
        persona = PersonaAutorizadaService.inactivate(persona_id)
        if not persona:
            return jsonify({'error': 'Persona autorizada no encontrada'}), 404
        return jsonify(persona.serialize()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@personas_api.route('/<int:persona_id>', methods=['DELETE'])
def eliminar_persona(persona_id):
    result = PersonaAutorizadaService.delete(persona_id)
    if not result:
        return jsonify({'error': 'Persona autorizada no encontrada'}), 404
    return jsonify({'message': 'Persona autorizada eliminada'}), 200