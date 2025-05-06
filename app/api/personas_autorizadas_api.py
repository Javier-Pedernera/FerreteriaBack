from flask import Blueprint, jsonify, request
from app import db
from app.models.persona_autorizada import PersonaAutorizada

personas_bp = Blueprint('personas_autorizadas_api', __name__)

@personas_bp.route('/', methods=['GET'])
def listar_personas():
    personas = PersonaAutorizada.query.all()
    return jsonify([p.serialize() for p in personas])

@personas_bp.route('/<int:persona_id>', methods=['GET'])
def obtener_persona(persona_id):
    persona = PersonaAutorizada.query.get_or_404(persona_id)
    return jsonify(persona.serialize())

@personas_bp.route('/', methods=['POST'])
def crear_persona():
    data = request.json
    persona = PersonaAutorizada(
        cliente_id=data['cliente_id'],
        nombre=data['nombre'],
        apellido=data['apellido'],
        dni=data.get('dni'),
        email=data.get('email'),
        telefono=data.get('telefono'),
        estado_id=data['estado_id']
    )
    db.session.add(persona)
    db.session.commit()
    return jsonify(persona.serialize()), 201
