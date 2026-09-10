from flask import Blueprint, jsonify

from app.models.tipo_comprobante import TipoComprobante
from app.models.condicion_iva import CondicionIVA
from app.models.tipo_documento import TipoDocumento

catalogos_api = Blueprint('catalogos_api', __name__)


@catalogos_api.route('/tipos-comprobante', methods=['GET'])
def get_tipos_comprobante():
    tipos = TipoComprobante.query.filter_by(activo=True).order_by(TipoComprobante.codigo_afip).all()
    return jsonify([t.serialize() for t in tipos]), 200


@catalogos_api.route('/condiciones-iva', methods=['GET'])
def get_condiciones_iva():
    condiciones = CondicionIVA.query.order_by(CondicionIVA.id).all()
    return jsonify([c.serialize() for c in condiciones]), 200


@catalogos_api.route('/tipos-documento', methods=['GET'])
def get_tipos_documento():
    tipos = TipoDocumento.query.filter_by(activo=True).order_by(TipoDocumento.codigo_afip).all()
    return jsonify([t.serialize() for t in tipos]), 200
