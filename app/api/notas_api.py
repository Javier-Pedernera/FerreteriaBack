from flask import Blueprint, request, jsonify

from app.services.nota_service import NotaService

notas_api = Blueprint('notas_api', __name__)


def _parse_bool(value):
    if value is None:
        return None
    return value.lower() in ('true', '1', 'si', 'sí')


@notas_api.route('', methods=['GET'])
def get_all():
    filtros = {
        'tipo_entidad': request.args.get('tipo_entidad'),
        'entidad_id': request.args.get('entidad_id', type=int),
        'leida': _parse_bool(request.args.get('leida')),
        'completada': _parse_bool(request.args.get('completada')),
        'usuario_asignado_id': request.args.get('usuario_asignado_id', type=int),
        'prioridad': request.args.get('prioridad'),
    }
    notas = NotaService.get_all_notas(filtros)
    return jsonify([n.serialize() for n in notas]), 200


@notas_api.route('/alertas', methods=['GET'])
def get_alertas():
    usuario_id = request.args.get('usuario_id', type=int)
    notas = NotaService.get_alertas(usuario_id)
    return jsonify([n.serialize() for n in notas]), 200


@notas_api.route('/<int:nota_id>', methods=['GET'])
def get(nota_id):
    nota = NotaService.get_nota_by_id(nota_id)
    if nota:
        return jsonify(nota.serialize()), 200
    return jsonify({'message': 'Nota no encontrada'}), 404


@notas_api.route('', methods=['POST'])
def create():
    data = request.get_json()
    try:
        nota = NotaService.create_nota(data)
        return jsonify(nota.serialize()), 201
    except ValueError as e:
        return jsonify({'message': str(e)}), 400
    except Exception as e:
        return jsonify({'message': str(e)}), 500


@notas_api.route('/<int:nota_id>', methods=['PUT'])
def update(nota_id):
    data = request.get_json()
    try:
        nota = NotaService.update_nota(nota_id, data)
        if nota:
            return jsonify(nota.serialize()), 200
        return jsonify({'message': 'Nota no encontrada'}), 404
    except ValueError as e:
        return jsonify({'message': str(e)}), 400


@notas_api.route('/<int:nota_id>/leer', methods=['PATCH'])
def marcar_leida(nota_id):
    data = request.get_json(silent=True) or {}
    nota = NotaService.marcar_leida(nota_id, data.get('leida', True))
    if nota:
        return jsonify(nota.serialize()), 200
    return jsonify({'message': 'Nota no encontrada'}), 404


@notas_api.route('/<int:nota_id>/completar', methods=['PATCH'])
def marcar_completada(nota_id):
    data = request.get_json(silent=True) or {}
    nota = NotaService.marcar_completada(nota_id, data.get('completada', True))
    if nota:
        return jsonify(nota.serialize()), 200
    return jsonify({'message': 'Nota no encontrada'}), 404


@notas_api.route('/<int:nota_id>', methods=['DELETE'])
def delete(nota_id):
    try:
        success = NotaService.delete_nota(nota_id)
        if success:
            return jsonify({'message': 'Nota eliminada'}), 200
        return jsonify({'message': 'Nota no encontrada'}), 404
    except ValueError as e:
        return jsonify({'message': str(e)}), 400
