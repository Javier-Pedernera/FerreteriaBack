from flask import Blueprint, jsonify, request
from app.services.unidad_medida_service import UnidadMedidaService

unidad_medida_bp = Blueprint('unidad_medida_api', __name__)

@unidad_medida_bp.route('/unidades-medida', methods=['GET'])
def listar_unidades():
    unidades = UnidadMedidaService.obtener_todas()
    return jsonify([u.serialize() for u in unidades])

@unidad_medida_bp.route('/unidades-medida/<int:unidad_id>', methods=['GET'])
def obtener_unidad(unidad_id):
    unidad = UnidadMedidaService.obtener_por_id(unidad_id)
    if unidad:
        return jsonify(unidad.serialize())
    return jsonify({'error': 'Unidad no encontrada'}), 404

@unidad_medida_bp.route('/unidades-medida', methods=['POST'])
def crear_unidad():
    data = request.json
    unidad = UnidadMedidaService.crear(data)
    return jsonify(unidad.serialize()), 201

@unidad_medida_bp.route('/unidades-medida/<int:unidad_id>', methods=['PUT'])
def actualizar_unidad(unidad_id):
    data = request.json
    unidad = UnidadMedidaService.actualizar(unidad_id, data)
    if unidad:
        return jsonify(unidad.serialize())
    return jsonify({'error': 'Unidad no encontrada'}), 404

@unidad_medida_bp.route('/unidades-medida/<int:unidad_id>', methods=['DELETE'])
def eliminar_unidad(unidad_id):
    eliminado = UnidadMedidaService.eliminar(unidad_id)
    if eliminado:
        return jsonify({'mensaje': 'Unidad eliminada'})
    return jsonify({'error': 'Unidad no encontrada'}), 404
