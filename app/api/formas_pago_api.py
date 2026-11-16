from flask import Blueprint, jsonify, request
from app import db
from app.models.forma_pago import FormaPago
from app.utils.local_media_service import LocalMediaService

formas_pago_bp = Blueprint('formas_pago_api', __name__)

CARPETA_FORMAS_PAGO = 'formas_pago'

@formas_pago_bp.route('/', methods=['GET'])
def listar_formas_pago():
    incluir_inactivas = request.args.get('incluir_inactivas', '').lower() in ('1', 'true')
    query = FormaPago.query
    if not incluir_inactivas:
        query = query.filter_by(activa=True)
    formas = query.order_by(FormaPago.nombre.asc()).all()
    return jsonify([f.serialize() for f in formas])

@formas_pago_bp.route('/<int:forma_id>', methods=['GET'])
def obtener_forma_pago(forma_id):
    forma = FormaPago.query.get_or_404(forma_id)
    return jsonify(forma.serialize())

@formas_pago_bp.route('/', methods=['POST'])
def crear_forma_pago():
    data = request.json

    icono_url = None
    if data.get('icono_base64'):
        icono_url = LocalMediaService.guardar_base64(data['icono_base64'], carpeta=CARPETA_FORMAS_PAGO)

    forma = FormaPago(
        nombre=data['nombre'],
        descripcion=data.get('descripcion'),
        activa=data.get('activa', True),
        icono=icono_url
    )
    db.session.add(forma)
    db.session.commit()
    return jsonify(forma.serialize()), 201

@formas_pago_bp.route('/<int:forma_id>', methods=['PUT'])
def actualizar_forma_pago(forma_id):
    forma = FormaPago.query.get_or_404(forma_id)
    data = request.json

    if 'nombre' in data:
        forma.nombre = data['nombre']
    if 'descripcion' in data:
        forma.descripcion = data['descripcion']
    if 'activa' in data:
        forma.activa = data['activa']

    if data.get('icono_base64'):
        icono_anterior = forma.icono
        forma.icono = LocalMediaService.guardar_base64(data['icono_base64'], carpeta=CARPETA_FORMAS_PAGO)
        LocalMediaService.eliminar(icono_anterior, carpeta=CARPETA_FORMAS_PAGO)
    elif 'icono' in data and data['icono'] is None:
        LocalMediaService.eliminar(forma.icono, carpeta=CARPETA_FORMAS_PAGO)
        forma.icono = None

    db.session.commit()
    return jsonify(forma.serialize())
