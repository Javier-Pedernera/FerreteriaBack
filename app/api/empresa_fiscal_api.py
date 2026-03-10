from flask import Blueprint, request, jsonify
from app.services.arca_service import ArcaService
from app.services.empresa_fiscal_service import EmpresaFiscalService

empresa_fiscal_api = Blueprint("empresa_fiscal_api", __name__)

# Obtener todas las empresas fiscales
@empresa_fiscal_api.route("/empresa-fiscal", methods=["GET"])
def get_all_empresas():
    empresas = EmpresaFiscalService.get_all()
    return jsonify([e.serialize() for e in empresas]), 200

# Obtener empresa por ID
@empresa_fiscal_api.route("/empresa-fiscal/<int:id>", methods=["GET"])
def get_empresa(id):
    try:
        empresa = EmpresaFiscalService.get_by_id(id)
        return jsonify(empresa.serialize()), 200
    except ValueError as e:
        return jsonify({"message": str(e)}), 404

# Crear nueva empresa fiscal
@empresa_fiscal_api.route("/empresa-fiscal", methods=["POST"])
def create_empresa():
    data = request.get_json()
    try:
        empresa = EmpresaFiscalService.create(data)
        return jsonify(empresa.serialize()), 201
    except Exception as e:
        return jsonify({"message": str(e)}), 400

# Actualizar empresa fiscal existente
@empresa_fiscal_api.route("/empresa-fiscal/<int:id>", methods=["PUT"])
def update_empresa(id):
    data = request.get_json()
    try:
        empresa = EmpresaFiscalService.update(id, data)
        return jsonify(empresa.serialize()), 200
    except ValueError as e:
        return jsonify({"message": str(e)}), 404
    except Exception as e:
        return jsonify({"message": str(e)}), 400
    

# =========================================
# TEST LOGIN ARCA (WSAA)
# =========================================
@empresa_fiscal_api.route("/empresa-fiscal/test-arca", methods=["GET"])
def test_login_arca():
    try:
        empresa = EmpresaFiscalService.get_empresa_activa()
        service = ArcaService(empresa)

        token, sign = service.obtener_token()

        return jsonify({
            "success": True,
            "message": "Login WSAA correcto",
            "token_preview": token[:25]  # mostramos solo parte
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500