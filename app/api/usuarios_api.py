from flask import Blueprint, jsonify, request
from app import db
from app.models.usuario import Usuario
from flask_jwt_extended import create_access_token
from flask_jwt_extended import create_access_token
from datetime import datetime
from app.services.usuario_service import registrar_usuario_service, login_usuario_service
from werkzeug.exceptions import HTTPException

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


@usuarios_bp.route('/register', methods=['POST'])
def registrar_usuario():
    try:
        data = request.json
        result = registrar_usuario_service(data)
        return jsonify(result), 201
    except HTTPException as e:
        return jsonify({"error": str(e)}), e.code

@usuarios_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.json
        result = login_usuario_service(data)
        return jsonify(result)
    except HTTPException as e:
        return jsonify({"error": str(e)}), e.code
    
@usuarios_bp.route('/<int:usuario_id>', methods=['PUT'])
def actualizar_usuario(usuario_id):
    usuario = Usuario.query.get_or_404(usuario_id)
    data = request.json

    usuario.nombre = data.get('nombre', usuario.nombre)
    usuario.apellido = data.get('apellido', usuario.apellido)
    usuario.email = data.get('email', usuario.email)
    usuario.telefono = data.get('telefono', usuario.telefono)
    usuario.estado_id = data.get('estado_id', usuario.estado_id)

    if 'password' in data:
        usuario.set_password(data['password'])

    db.session.commit()
    return jsonify(usuario.serialize())

@usuarios_bp.route('/<int:usuario_id>', methods=['DELETE'])
def eliminar_usuario(usuario_id):
    usuario = Usuario.query.get_or_404(usuario_id)
    db.session.delete(usuario)
    db.session.commit()
    return jsonify({"mensaje": "Usuario eliminado"}), 200