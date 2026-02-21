from flask import Blueprint, request, jsonify

from app.services.facturacion_service import FacturacionService
from app.models.factura import Factura

facturacion_api = Blueprint('facturacion_api', __name__)


# --------------------------------------------------
# CREAR FACTURA DESDE VENTAS
# --------------------------------------------------
@facturacion_api.route('/facturas', methods=['POST'])
def crear_factura():
    data = request.get_json()

    cliente_id = data.get("cliente_id")
    ventas_ids = data.get("ventas_ids")

    if not cliente_id or not ventas_ids:
        return jsonify({
            "message": "cliente_id y ventas_ids son obligatorios"
        }), 400

    try:
        factura = FacturacionService.crear_factura_desde_ventas(
            cliente_id,
            ventas_ids
        )

        return jsonify(factura.serialize()), 201

    except ValueError as e:
        return jsonify({"message": str(e)}), 400

    except Exception as e:
        return jsonify({
            "message": "Error al crear factura",
            "error": str(e)
        }), 500


# --------------------------------------------------
# OBTENER FACTURA POR ID
# --------------------------------------------------
@facturacion_api.route('/facturas/<int:id>', methods=['GET'])
def get_factura(id):
    factura = Factura.query.get(id)

    if factura:
        return jsonify(factura.serialize()), 200

    return jsonify({'message': 'Factura no encontrada'}), 404


# --------------------------------------------------
# LISTAR FACTURAS
# --------------------------------------------------
@facturacion_api.route('/facturas', methods=['GET'])
def get_all_facturas():
    facturas = Factura.query.order_by(Factura.id.desc()).all()
    return jsonify([f.serialize() for f in facturas]), 200


# --------------------------------------------------
# EMITIR FACTURA EN ARCA
# --------------------------------------------------
@facturacion_api.route('/facturas/<int:id>/emitir', methods=['POST'])
def emitir_factura(id):
    try:
        factura = FacturacionService.emitir_factura_arca(id)
        return jsonify(factura.serialize()), 200

    except ValueError as e:
        return jsonify({"message": str(e)}), 400

    except Exception as e:
        return jsonify({
            "message": "Error al emitir factura",
            "error": str(e)
        }), 500