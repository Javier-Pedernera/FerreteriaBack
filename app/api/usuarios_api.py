from flask import Blueprint, jsonify, request
from app import db
from app.models.usuario import Usuario

usuarios_bp = Blueprint('usuarios_api', __name__)

@usuarios_bp.route('/', methods=['GET'])
def listar_usuarios():
    usuarios = Usuario.query.all()
    return jsonify([u.serialize() for u in usuarios])

@usuarios_bp.route('/<int:usuario_id>', methods=['GET'])
def obtener_usuario(usuario_id):
    usuario = Usuario.query.get_or_404(usuario_id)
    return jsonify(usuario.serialize())

@usuarios_bp.route('/', methods=['POST'])
def crear_usuario():
    data = request.json
    usuario = Usuario(
        nombre=data['nombre'],
        apellido=data.get('apellido'),
        email=data.get('email'),
        telefono=data.get('telefono'),
        estado_id=data['estado_id']
    )
    db.session.add(usuario)
    db.session.commit()
    return jsonify(usuario.serialize()), 201
