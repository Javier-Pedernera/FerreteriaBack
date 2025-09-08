from flask import Blueprint, request, jsonify
from app.services.cuenta_service import CuentaService
from app.services.movimiento_service import MovimientoService

cuentas_api = Blueprint('cuentas_api', __name__, url_prefix='/api/cuentas')

# --- Cuentas ---
@cuentas_api.route('/', methods=['GET'])
def get_cuentas():
    return jsonify(CuentaService.get_all_cuentas())

@cuentas_api.route('/<int:cuenta_id>', methods=['GET'])
def get_cuenta(cuenta_id):
    return jsonify(CuentaService.get_cuenta_by_id(cuenta_id))

@cuentas_api.route('/', methods=['POST'])
def create_cuenta():
    data = request.get_json()
    return jsonify(CuentaService.create_cuenta(data))

@cuentas_api.route('/<int:cuenta_id>', methods=['PUT'])
def update_cuenta(cuenta_id):
    data = request.get_json()
    return jsonify(CuentaService.update_cuenta(cuenta_id, data))

# --- Movimientos ---
@cuentas_api.route('/<int:cuenta_id>/movimientos', methods=['GET'])
def get_movimientos(cuenta_id):
    return jsonify(MovimientoService.get_movimientos(cuenta_id))

@cuentas_api.route('/<int:cuenta_id>/movimientos', methods=['POST'])
def create_movimiento(cuenta_id):
    data = request.get_json()
    return jsonify(MovimientoService.create_movimiento(cuenta_id, data))