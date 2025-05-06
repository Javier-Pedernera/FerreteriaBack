from flask import Blueprint, jsonify, request
from app import db
from app.models.forma_pago import FormaPago

formas_pago_bp = Blueprint('formas_pago_api', __name__)

@formas_pago_bp.route('/', methods=['GET'])
def listar_formas_pago():
    formas = FormaPago.query.all()
    return jsonify([f.serialize() for f in formas])

@formas_pago_bp.route('/<int:forma_id>', methods=['GET'])
def obtener_forma_pago(forma_id):
    forma = FormaPago.query.get_or_404(forma_id)
    return jsonify(forma.serialize())

@formas_pago_bp.route('/', methods=['POST'])
def crear_forma_pago():
    data = request.json
    forma = FormaPago(
        nombre=data['nombre'],
        descripcion=data.get('descripcion')
    )
    db.session.add(forma)
    db.session.commit()
    return jsonify(forma.serialize()), 201
