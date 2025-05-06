from flask import Blueprint, request, jsonify
from app.services.categoria_service import CategoriaService

categoria_api = Blueprint('categoria_api', __name__)

@categoria_api.route('/categorias', methods=['GET'])
def listar_categorias():
    categorias = CategoriaService.get_all_categorias()
    return jsonify([c.serialize() for c in categorias]), 200

@categoria_api.route('/categorias/<int:categoria_id>', methods=['GET'])
def obtener_categoria(categoria_id):
    categoria = CategoriaService.get_categoria_by_id(categoria_id)
    if not categoria:
        return jsonify({'error': 'Categoría no encontrada'}), 404
    return jsonify(categoria.serialize()), 200

@categoria_api.route('/categorias', methods=['POST'])
def crear_categoria():
    data = request.json
    categoria = CategoriaService.create_categoria(data)
    return jsonify(categoria.serialize()), 201

@categoria_api.route('/categorias/<int:categoria_id>', methods=['PUT'])
def actualizar_categoria(categoria_id):
    data = request.json
    categoria = CategoriaService.update_categoria(categoria_id, data)
    if not categoria:
        return jsonify({'error': 'Categoría no encontrada'}), 404
    return jsonify(categoria.serialize()), 200

@categoria_api.route('/categorias/<int:categoria_id>', methods=['DELETE'])
def eliminar_categoria(categoria_id):
    categoria = CategoriaService.delete_categoria(categoria_id)
    if not categoria:
        return jsonify({'error': 'Categoría no encontrada'}), 404
    return jsonify({'message': 'Categoría eliminada'}), 200
