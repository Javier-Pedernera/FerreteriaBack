from flask import Blueprint, request, jsonify
from app.services.pedido_service import PedidoService

pedido_bp = Blueprint("pedido_bp", __name__)

@pedido_bp.route("/pedidos-proveedores", methods=["GET"])
def listar_pedidos():
    page = request.args.get("page", default=1, type=int)
    limit = request.args.get("limit", default=15, type=int)
    estado_code = request.args.get("estado", type=str)

    return PedidoService.get_pedidos_paginados(page=page, limit=limit, estado_code=estado_code), 200

@pedido_bp.route("/pedidos-proveedores/<int:pedido_id>", methods=["GET"])
def obtener_pedido(pedido_id):
    pedido = PedidoService.get_pedido_by_id(pedido_id)
    if not pedido:
        return jsonify({"error": "Pedido no encontrado"}), 404
    return jsonify(pedido), 200

@pedido_bp.route("/pedidos-proveedores", methods=["POST"])
def crear_pedido():
    data = request.get_json()
    print(data)
    if not data:
        return jsonify({"error": "Datos JSON faltantes o mal formateados"}), 400

    try:
        nuevo_pedido = PedidoService.crear_pedido(data)
        return jsonify(nuevo_pedido), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@pedido_bp.route("/pedidos-proveedores/<int:pedido_id>/estado", methods=["PUT"])
def cambiar_estado(pedido_id):
    data = request.json
    nuevo_estado_id = data.get("estado_id")
    numero_factura = data.get("numero_factura")

    try:
        pedido_actualizado = PedidoService.actualizar_estado_pedido(pedido_id, nuevo_estado_id, numero_factura)
        if not pedido_actualizado:
            return jsonify({"error": "Pedido no encontrado"}), 404
        return jsonify(pedido_actualizado), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@pedido_bp.route("/pedidos-proveedores/pendiente/<int:proveedor_id>", methods=["GET"])
def pedido_pendiente_proveedor(proveedor_id):
    pedido = PedidoService.obtener_pedido_pendiente_por_proveedor(proveedor_id)
    if pedido is None:
        return jsonify(None), 200 
    return jsonify(pedido), 200