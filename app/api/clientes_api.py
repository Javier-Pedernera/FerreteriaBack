from flask import Blueprint, jsonify, request
from app import db
from app.models.cliente import Cliente
from app.services.cliente_service import ClienteService
from app.services.pago_service import PagoService
from app.services.resumen_cuenta_corriente import ResumenCuentaCorrienteService

clientes_bp = Blueprint('clientes_api', __name__)

@clientes_bp.route('/', methods=['GET'])
def listar_clientes():
    clientes = ClienteService.get_all_clientes()
    return jsonify([c.serialize() for c in clientes]), 200

@clientes_bp.route('/<int:cliente_id>', methods=['GET'])
def obtener_cliente(cliente_id):
    cliente = ClienteService.get_cliente_by_id(cliente_id)
    if not cliente:
        return jsonify({'error': 'Cliente no encontrado'}), 404
    return jsonify(cliente.serialize()), 200

@clientes_bp.route('/', methods=['POST'])
def crear_cliente():
    data = request.json
    cliente = ClienteService.create_cliente(data)
    return jsonify(cliente.serialize()), 201

@clientes_bp.route('/<int:cliente_id>', methods=['PUT'])
def actualizar_cliente(cliente_id):
    data = request.json
    cliente = ClienteService.update_cliente(cliente_id, data)
    if not cliente:
        return jsonify({'error': 'Cliente no encontrado'}), 404
    return jsonify(cliente.serialize()), 200

@clientes_bp.route('/<int:cliente_id>/deuda', methods=['GET'])
def cliente_deuda(cliente_id):
    desde = request.args.get("desde")
    hasta = request.args.get("hasta")

    try:
        data = ClienteService.get_cliente_con_deuda(
            cliente_id=cliente_id,
            desde=desde,
            hasta=hasta
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    if not data:
        return jsonify({"error": "Cliente no encontrado"}), 404

    return jsonify(data), 200

@clientes_bp.route('/<int:cliente_id>/pagos', methods=['POST'])
def registrar_pago(cliente_id):
    data = request.json
    monto = data.get('monto')
    forma_pago_id = data.get('forma_pago_id')
    observaciones = data.get('observaciones')
    usar_saldo_favor = data.get('usar_saldo_favor', False)

    if monto is None:
        return jsonify({"error": "El monto es obligatorio"}), 400

    # Registrar el pago usando el servicio
    pago, restante = PagoService.registrar_pago_cliente(
        cliente_id=cliente_id,
        monto=monto,
        forma_pago_id=forma_pago_id,
        observaciones=observaciones,
        usar_saldo_favor=usar_saldo_favor
    )

    cliente = Cliente.query.get(cliente_id)

    # Serializar el pago
    pago_serializado = {
        "id": pago.id,
        "cliente_id": pago.cliente_id,
        "monto": float(pago.monto),
        "forma_pago_id": pago.forma_pago_id,
        "observaciones": pago.observaciones,
        "fecha": pago.fecha.isoformat() if pago.fecha else None
    }

    return jsonify({
        "pago": pago_serializado,
        "restante": float(restante),
        "saldo_favor": float(cliente.saldo_favor or 0)
    }), 200
    
@clientes_bp.route('/<int:cliente_id>/resumen', methods=['GET'])
def cliente_resumen(cliente_id):
    desde = request.args.get("desde")
    hasta = request.args.get("hasta")

    try:
        data = ClienteService.get_resumen_cuenta_corriente(
            cliente_id=cliente_id,
            desde=desde,
            hasta=hasta
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    if not data:
        return jsonify({"error": "Cliente no encontrado"}), 404

    return jsonify(data), 200

# @clientes_bp.route('/<int:cliente_id>/resumen_para_cliente', methods=['GET'])
# def resumen_para_cliente(cliente_id):
#     data = ClienteService.get_resumen_para_cliente(cliente_id)

#     if not data:
#         return jsonify({"error": "Cliente no encontrado"}), 404

#     return jsonify(data), 200

@clientes_bp.route('/<int:cliente_id>/resumen_para_cliente', methods=['GET'])
def resumen_para_cliente(cliente_id):
    desde = request.args.get("desde")
    hasta = request.args.get("hasta")
    solo_cc = request.args.get("solo_cuenta_corriente", "false").lower() == "true"

    if not desde or not hasta:
        return jsonify({
            "error": "Los parámetros 'desde' y 'hasta' son obligatorios (YYYY-MM-DD)"
        }), 400

    try:
        data = ResumenCuentaCorrienteService.get_resumen_para_cliente(
            cliente_id=cliente_id,
            desde=desde,
            hasta=hasta,
            solo_cuenta_corriente=solo_cc
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    if not data:
        return jsonify({"error": "Cliente no encontrado"}), 404

    return jsonify(data), 200

@clientes_bp.route('/<int:cliente_id>/movimientos/ajuste', methods=['POST'])
def crear_ajuste_migracion(cliente_id):
    data = request.get_json()

    if not data:
        return jsonify({"error": "Body requerido"}), 400

    diferencia = data.get("diferencia")
    deuda_legacy = data.get("deuda_legacy")
    deuda_movimientos = data.get("deuda_movimientos")
    saldo_favor = data.get("saldo_favor")

    if diferencia is None:
        return jsonify({"error": "diferencia es obligatoria"}), 400

    try:
        movimiento = ClienteService.crear_ajuste(
            cliente_id=cliente_id,
            diferencia=float(diferencia),
            deuda_legacy=deuda_legacy,
            deuda_movimientos=deuda_movimientos,
            saldo_favor=saldo_favor
        )

        return jsonify(movimiento), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400