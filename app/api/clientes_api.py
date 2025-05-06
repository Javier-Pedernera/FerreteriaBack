from flask import Blueprint, jsonify, request
from app import db
from app.models.cliente import Cliente

clientes_bp = Blueprint('clientes_api', __name__)

@clientes_bp.route('/', methods=['GET'])
def listar_clientes():
    clientes = Cliente.query.all()
    return jsonify([c.serialize() for c in clientes])

@clientes_bp.route('/<int:cliente_id>', methods=['GET'])
def obtener_cliente(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)
    return jsonify(cliente.serialize())

@clientes_bp.route('/', methods=['POST'])
def crear_cliente():
    data = request.json
    cliente = Cliente(
        nombre=data['nombre'],
        razon_social=data.get('razon_social'),
        cuit=data.get('cuit'),
        email=data.get('email'),
        telefono=data.get('telefono'),
        direccion=data.get('direccion'),
        estado_id=data['estado_id']
    )
    db.session.add(cliente)
    db.session.commit()
    return jsonify(cliente.serialize()), 201