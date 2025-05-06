from flask import Blueprint, request, jsonify
from app.models.proveedor import Proveedor
from app import db
from  app.services.proveedor_service import ProveedorService

api_proveedor = Blueprint('api_proveedor', __name__)

@api_proveedor.route('/proveedores', methods=['POST'])
def create_proveedor():
    data = request.get_json()
    proveedor = ProveedorService.create_proveedor(data)
    return jsonify(proveedor.serialize()), 201

@api_proveedor.route('/proveedores/<int:id>', methods=['PUT'])
def update_proveedor(id):
    data = request.get_json()
    proveedor = ProveedorService.update_proveedor(id, data)
    if proveedor:
        return jsonify(proveedor.serialize())
    return jsonify({'message': 'Proveedor not found'}), 404

@api_proveedor.route('/proveedores/<int:id>', methods=['GET'])
def get_proveedor(id):
    proveedor = ProveedorService.get_proveedor(id)
    if proveedor:
        return jsonify(proveedor.serialize())
    return jsonify({'message': 'Proveedor not found'}), 404

@api_proveedor.route('/proveedores', methods=['GET'])
def get_all_proveedores():
    proveedores = ProveedorService.get_all_proveedores()
    return jsonify([proveedor.serialize() for proveedor in proveedores])

@api_proveedor.route('/proveedores/<int:id>', methods=['DELETE'])
def delete_proveedor(id):
    success = ProveedorService.delete_proveedor(id)
    if success:
        return jsonify({'message': 'Proveedor deleted'}), 204
    return jsonify({'message': 'Proveedor not found'}), 404
