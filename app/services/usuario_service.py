from app import db
from app.models.usuario import Usuario
from flask_jwt_extended import create_access_token
from datetime import datetime, timezone
from werkzeug.exceptions import BadRequest, Unauthorized

def registrar_usuario_service(data):
    if Usuario.query.filter_by(email=data['email']).first():
        raise BadRequest("El email ya está registrado")

    usuario = Usuario(
        nombre=data['nombre'],
        apellido=data.get('apellido'),
        email=data['email'],
        telefono=data.get('telefono'),
        estado_id=data['estado_id'],
        creado_en=datetime.now(timezone.utc)
    )
    usuario.set_password(data['password'])

    db.session.add(usuario)
    db.session.commit()

    token = create_access_token(identity=usuario.id)

    return {
        "usuario": usuario.serialize(),
        "access_token": token
    }

def login_usuario_service(data):
    usuario = Usuario.query.filter_by(email=data['email']).first()
    if not usuario or not usuario.check_password(data['password']):
        raise Unauthorized("Credenciales inválidas")

    token = create_access_token(identity=usuario.id)

    return {
        "usuario": usuario.serialize(),
        "access_token": token
    }