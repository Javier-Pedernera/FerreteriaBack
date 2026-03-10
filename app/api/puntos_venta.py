from flask import Blueprint, request, jsonify
from app.services.punto_venta_service import PuntoVentaService

puntos_venta_bp = Blueprint('puntos_venta', __name__)


@puntos_venta_bp.route("", methods=["POST"])
def crear_punto_venta():
    try:

        data = request.get_json()

        pv = PuntoVentaService.crear_punto_venta(data)

        return jsonify({
            "ok": True,
            "data": pv.serialize()
        }), 201

    except Exception as e:

        return jsonify({
            "ok": False,
            "error": str(e)
        }), 400


@puntos_venta_bp.route("/empresa/<int:empresa_id>", methods=["GET"])
def obtener_puntos_empresa(empresa_id):
    try:

        puntos = PuntoVentaService.obtener_puntos_empresa(empresa_id)

        return jsonify({
            "ok": True,
            "data": [p.serialize() for p in puntos]
        })

    except Exception as e:

        return jsonify({
            "ok": False,
            "error": str(e)
        }), 400


@puntos_venta_bp.route("/<int:pv_id>", methods=["DELETE"])
def eliminar_punto_venta(pv_id):
    try:

        PuntoVentaService.eliminar_punto_venta(pv_id)

        return jsonify({
            "ok": True
        })

    except Exception as e:

        return jsonify({
            "ok": False,
            "error": str(e)
        }), 400