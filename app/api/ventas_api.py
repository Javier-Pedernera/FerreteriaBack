from flask import Blueprint, request, jsonify
from app.services.ventas_service import VentaService
from decimal import Decimal

ventas_api = Blueprint('ventas_api', __name__)


@ventas_api.route('/', methods=['POST'])
def crear():
    data = request.get_json()
    try:
        nueva_venta = VentaService.crear_venta(data)
        return jsonify(nueva_venta), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@ventas_api.route('/', methods=['GET'])
def listar():
    estado = request.args.get('estado')
    fecha = request.args.get('fecha')
    page = int(request.args.get('page', 1))

    try:
        ventas_data = VentaService.obtener_filtradas(estado, fecha, page)
        return jsonify(ventas_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    
@ventas_api.route('/<int:venta_id>', methods=['GET'])
def obtener(venta_id):
    try:
        venta = VentaService.obtener_por_id(venta_id)
        return jsonify(venta)
    except Exception as e:
        return jsonify({'error': str(e)}), 404

# @ventas_api.route('/', methods=['GET'])
# def listar():
#     ventas = VentaService.obtener_todas_las_ventas()
#     return jsonify(ventas)

# @ventas_api.route('/<int:venta_id>', methods=['PUT'])
# def actualizar(venta_id):
#     data = request.get_json()
#     try:
#         venta_actualizada = VentaService.actualizar_venta(venta_id, data)
#         return jsonify(venta_actualizada)
#     except Exception as e:
#         return jsonify({'error': str(e)}), 400

@ventas_api.route('/<int:venta_id>/eliminar', methods=['PUT'])
def eliminar_logico(venta_id):
    try:
        venta = VentaService.eliminar_logico(venta_id)
        return jsonify(venta), 200
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

@ventas_api.route('/tiene-en-proceso/<int:cliente_id>', methods=['GET'])
def cliente_tiene_en_proceso(cliente_id):
    try:
        tiene = VentaService.cliente_tiene_venta_en_proceso(cliente_id)
        return jsonify({"tiene_en_proceso": tiene})
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    
@ventas_api.route('/<int:venta_id>', methods=['PUT'])
def update_venta(venta_id):
    data = request.json
    venta_actualizada = VentaService.actualizar_venta(venta_id, data)
    return jsonify(venta_actualizada.serialize()), 200

@ventas_api.route('/<int:venta_id>/cobrar', methods=['PUT'])
def cobrar_venta(venta_id):
    data = request.get_json()
    forma_pago_id = data.get('forma_pago_id')
    monto_abonado = data.get('monto_abonado')
    persona_autorizada_id = data.get('persona_autorizada_id')
    observaciones = data.get('observaciones')
    recargo_tarjeta = data.get('recargo_tarjeta')
    descuento_aplicado = data.get('descuento_aplicado')
    if not forma_pago_id or monto_abonado is None:
        return jsonify({"error": "forma_pago_id y monto_abonado son requeridos"}), 400

    try:
        venta_cobrada = VentaService.cobrar_venta(
            venta_id,
            forma_pago_id,
            float(monto_abonado),
            persona_autorizada_id,
            observaciones,
            float(recargo_tarjeta) if recargo_tarjeta is not None else 0,
            float(descuento_aplicado) if descuento_aplicado is not None else 0
        )
        return jsonify(venta_cobrada), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400