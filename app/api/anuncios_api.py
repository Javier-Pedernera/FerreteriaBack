from flask import Blueprint, request, jsonify

from app.services.anuncio_service import AnuncioService

anuncios_api = Blueprint('anuncios_api', __name__)


@anuncios_api.route('', methods=['GET'])
def get_all():
    filtros = {'posicion': request.args.get('posicion')}
    anuncios = AnuncioService.get_all(filtros)
    return jsonify([a.serialize() for a in anuncios]), 200


@anuncios_api.route('/publicos', methods=['GET'])
def get_publicos():
    """Endpoint público (sin auth) que consume la pantalla del TV."""
    return jsonify(AnuncioService.get_publicos()), 200


@anuncios_api.route('/<int:anuncio_id>', methods=['GET'])
def get(anuncio_id):
    anuncio = AnuncioService.get_by_id(anuncio_id)
    if anuncio:
        return jsonify(anuncio.serialize()), 200
    return jsonify({'message': 'Anuncio no encontrado'}), 404


@anuncios_api.route('', methods=['POST'])
def create():
    data = request.get_json()
    try:
        anuncio = AnuncioService.create(data)
        return jsonify(anuncio.serialize()), 201
    except ValueError as e:
        return jsonify({'message': str(e)}), 400
    except Exception as e:
        return jsonify({'message': str(e)}), 500


@anuncios_api.route('/<int:anuncio_id>', methods=['PUT'])
def update(anuncio_id):
    data = request.get_json()
    try:
        anuncio = AnuncioService.update(anuncio_id, data)
        if anuncio:
            return jsonify(anuncio.serialize()), 200
        return jsonify({'message': 'Anuncio no encontrado'}), 404
    except ValueError as e:
        return jsonify({'message': str(e)}), 400
    except Exception as e:
        return jsonify({'message': str(e)}), 500


@anuncios_api.route('/reordenar', methods=['PATCH'])
def reordenar():
    data = request.get_json() or {}
    orden_ids = data.get('orden_ids', [])
    if not isinstance(orden_ids, list):
        return jsonify({'message': "'orden_ids' debe ser una lista de ids"}), 400
    AnuncioService.reordenar(orden_ids)
    return jsonify({'message': 'Orden actualizado'}), 200


@anuncios_api.route('/<int:anuncio_id>', methods=['DELETE'])
def delete(anuncio_id):
    try:
        success = AnuncioService.delete(anuncio_id)
        if success:
            return jsonify({'message': 'Anuncio eliminado'}), 200
        return jsonify({'message': 'Anuncio no encontrado'}), 404
    except Exception as e:
        return jsonify({'message': str(e)}), 500
