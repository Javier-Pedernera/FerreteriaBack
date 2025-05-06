from flask import Blueprint, request, jsonify
from app.services.marca_service import MarcaService

marca_api = Blueprint('marca_api', __name__)

@marca_api.route('/marcas', methods=['GET'])
def get_all():
    marcas = MarcaService.get_all_marcas()
    return jsonify([marca.serialize() for marca in marcas]), 200

@marca_api.route('/marcas/<int:id>', methods=['GET'])
def get(id):
    marca = MarcaService.get_marca_by_id(id)
    if marca:
        return jsonify(marca.serialize()), 200
    return jsonify({'message': 'Marca no encontrada'}), 404

@marca_api.route('/marcas', methods=['POST'])
def create():
    data = request.get_json()
    try:
        new_marca = MarcaService.create_marca(data)
        return jsonify(new_marca.serialize()), 201
    except Exception as e:
        return jsonify({'message': str(e)}), 400

@marca_api.route('/marcas/<int:id>', methods=['PUT'])
def update(id):
    data = request.get_json()
    updated_marca = MarcaService.update_marca(id, data)
    if updated_marca:
        return jsonify(updated_marca.serialize()), 200
    return jsonify({'message': 'Marca no encontrada'}), 404

@marca_api.route('/marcas/<int:id>', methods=['DELETE'])
def delete(id):
    success = MarcaService.delete_marca(id)
    if success:
        return jsonify({'message': 'Marca eliminada'}), 200
    return jsonify({'message': 'Marca no encontrada'}), 404
