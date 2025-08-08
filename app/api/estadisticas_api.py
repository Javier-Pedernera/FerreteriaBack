from datetime import date, datetime
from flask import Blueprint, jsonify, request
from app.services.estadisticas_service import EstadisticasService

estadisticas_bp = Blueprint('estadisticas_api', __name__)

# GET /estadisticas/ventas?periodo=diario|mensual|anual
@estadisticas_bp.route('/ventas', methods=['GET'])
def listar_ventas_por_periodo():
    periodo = request.args.get('periodo', 'diario')
    data = EstadisticasService.ventas_por_periodo(periodo)
    return jsonify(data), 200

# GET /estadisticas/clientes/top?limite=10
@estadisticas_bp.route('/clientes-top', methods=['GET'])
def listar_clientes_top():
    limite = int(request.args.get('limite', 10))
    data = EstadisticasService.top_clientes(limite)
    return jsonify(data), 200

# GET /estadisticas/ventas/cliente/<id>?periodo=diario|mensual|anual
@estadisticas_bp.route('/ventas/cliente/<int:cliente_id>', methods=['GET'])
def listar_ventas_por_cliente(cliente_id):
    periodo = request.args.get('periodo', 'diario')
    data = EstadisticasService.ventas_cliente(cliente_id, periodo)
    return jsonify(data), 200

@estadisticas_bp.route('/resumen', methods=['GET'])
def resumen_estadisticas():
    data = EstadisticasService.resumen()
    return jsonify(data), 200

@estadisticas_bp.route('/finanzas/resumen', methods=['GET'])
def resumen_ingresos_egresos():
    fecha_str = request.args.get('fecha')
    if fecha_str:
        try:
            fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({"error": "Formato de fecha inválido, debe ser YYYY-MM-DD"}), 400
    else:
        fecha = date.today()

    data = EstadisticasService.resumen_ingresos_egresos_diarios(fecha)
    return jsonify(data), 200