from flask import Blueprint, request, jsonify

from app.services.presupuesto_service import PresupuestoService

presupuestos_api = Blueprint('presupuestos_api', __name__)


@presupuestos_api.route('', methods=['GET'])
def get_all():
    filtros = {
        'query': request.args.get('query'),
        'estado': request.args.get('estado'),
    }
    presupuestos = PresupuestoService.get_all_presupuestos(filtros)
    return jsonify([p.serialize() for p in presupuestos]), 200


@presupuestos_api.route('/<int:presupuesto_id>', methods=['GET'])
def get(presupuesto_id):
    presupuesto = PresupuestoService.get_presupuesto_by_id(presupuesto_id)
    if presupuesto:
        return jsonify(presupuesto.serialize()), 200
    return jsonify({'message': 'Presupuesto no encontrado'}), 404


@presupuestos_api.route('', methods=['POST'])
def create():
    data = request.get_json()
    try:
        presupuesto = PresupuestoService.create_presupuesto(data)
        return jsonify(presupuesto.serialize()), 201
    except ValueError as e:
        return jsonify({'message': str(e)}), 400
    except Exception as e:
        return jsonify({'message': str(e)}), 500


@presupuestos_api.route('/<int:presupuesto_id>', methods=['PUT'])
def update(presupuesto_id):
    data = request.get_json()
    try:
        presupuesto = PresupuestoService.update_presupuesto(presupuesto_id, data)
        if presupuesto:
            return jsonify(presupuesto.serialize()), 200
        return jsonify({'message': 'Presupuesto no encontrado'}), 404
    except ValueError as e:
        return jsonify({'message': str(e)}), 400


@presupuestos_api.route('/<int:presupuesto_id>/estado', methods=['PATCH'])
def cambiar_estado(presupuesto_id):
    data = request.get_json(silent=True) or {}
    try:
        presupuesto = PresupuestoService.cambiar_estado(presupuesto_id, data.get('estado'))
        if presupuesto:
            return jsonify(presupuesto.serialize()), 200
        return jsonify({'message': 'Presupuesto no encontrado'}), 404
    except ValueError as e:
        return jsonify({'message': str(e)}), 400


@presupuestos_api.route('/<int:presupuesto_id>/convertir', methods=['PATCH'])
def convertir(presupuesto_id):
    data = request.get_json(silent=True) or {}
    try:
        presupuesto = PresupuestoService.convertir_en_venta(presupuesto_id, data.get('venta_id'))
        if presupuesto:
            return jsonify(presupuesto.serialize()), 200
        return jsonify({'message': 'Presupuesto no encontrado'}), 404
    except ValueError as e:
        return jsonify({'message': str(e)}), 400


@presupuestos_api.route('/<int:presupuesto_id>', methods=['DELETE'])
def delete(presupuesto_id):
    success = PresupuestoService.delete_presupuesto(presupuesto_id)
    if success:
        return jsonify({'message': 'Presupuesto eliminado'}), 200
    return jsonify({'message': 'Presupuesto no encontrado'}), 404
