from flask import Blueprint, request, jsonify
from app.services.ventas_service import VentaService

ventas_api = Blueprint('ventas_api', __name__)

@ventas_api.route('/', methods=['POST'])
def crear():
    data = request.get_json()
    try:
        nueva_venta = VentaService.crear_venta(data)
        return jsonify(nueva_venta), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@ventas_api.route('/<int:venta_id>', methods=['GET'])
def obtener(venta_id):
    try:
        venta = VentaService.obtener_venta(venta_id)
        return jsonify(venta)
    except Exception as e:
        return jsonify({'error': str(e)}), 404

@ventas_api.route('/', methods=['GET'])
def listar():
    ventas = VentaService.obtener_todas_las_ventas()
    return jsonify(ventas)

@ventas_api.route('/<int:venta_id>', methods=['PUT'])
def actualizar(venta_id):
    data = request.get_json()
    try:
        venta_actualizada = VentaService.actualizar_venta(venta_id, data)
        return jsonify(venta_actualizada)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@ventas_api.route('/<int:venta_id>', methods=['DELETE'])
def eliminar(venta_id):
    try:
        result = VentaService.eliminar_venta(venta_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    
@ventas_api.route('/aplicar_pago', methods=['POST'])
def pagar_ventas_en_cuenta():
    data = request.get_json()
    cliente_id = data.get('cliente_id')
    monto_pagado = data.get('monto_pagado')

    if not cliente_id or monto_pagado is None:
        return jsonify({"error": "cliente_id y monto_pagado son requeridos"}), 400

    try:
        ventas_actualizadas = VentaService.aplicar_pago_a_cuenta(cliente_id, float(monto_pagado))
        return jsonify({"ventas_pagadas": ventas_actualizadas}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
