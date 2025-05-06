from flask import Blueprint, request, jsonify
from app.services.import_template_service import import_products_from_excel
from app.services.producto_service import ProductoService

producto_api = Blueprint('producto_api', __name__)

@producto_api.route('/productos', methods=['GET'])
def get_productos():
    productos = ProductoService.obtener_todos()
    return jsonify([p.serialize() for p in productos]), 200

@producto_api.route('/productos/<int:id>', methods=['GET'])
def get_producto(id):
    producto = ProductoService.obtener_por_id(id)
    return jsonify(producto.serialize()), 200

@producto_api.route('/productos', methods=['POST'])
def post_producto():
    data = request.get_json()
    try:
        producto = ProductoService.crear(data)
        return jsonify(producto.serialize()), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@producto_api.route('/productos/<int:id>', methods=['PUT'])
def put_producto(id):
    data = request.get_json()
    try:
        producto = ProductoService.actualizar(id, data)
        return jsonify(producto.serialize()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@producto_api.route('/productos/<int:id>', methods=['DELETE'])
def delete_producto(id):
    try:
        ProductoService.eliminar(id)
        return jsonify({'message': 'Producto eliminado'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    
@producto_api.route('/productos/importar', methods=['POST'])
def importar_productos():
    data = request.get_json()

    if not data.get('plantilla_id'):
        return jsonify({"error": "plantilla_id is required"}), 400

    # Llamada al servicio con el ID de la plantilla
    result = import_products_from_excel(data['plantilla_id'], data['cotizacion_dolar'], data['fecha_lista'])

    if result.get("error"):
        return jsonify({"error": result["error"]}), 500

    return jsonify({
        "message": "Products imported successfully",
        "processed_count": result["processed_count"],
        "errors": result["errors"]
    }), 200