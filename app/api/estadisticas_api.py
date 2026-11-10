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

# GET /estadisticas/ganancia-mensual
@estadisticas_bp.route('/ganancia-mensual', methods=['GET'])
def listar_ganancia_mensual():
    data = EstadisticasService.ganancia_mensual()
    return jsonify(data), 200

# GET /estadisticas/formas-pago?mes=YYYY-MM
@estadisticas_bp.route('/formas-pago', methods=['GET'])
def listar_ventas_por_forma_pago():
    mes = request.args.get('mes')
    data = EstadisticasService.ventas_por_forma_pago(mes)
    return jsonify(data), 200

# GET /estadisticas/productos-top?limite=10&mes=YYYY-MM
@estadisticas_bp.route('/productos-top', methods=['GET'])
def listar_productos_mas_vendidos():
    limite = int(request.args.get('limite', 10))
    mes = request.args.get('mes')
    data = EstadisticasService.productos_mas_vendidos(limite, mes)
    return jsonify(data), 200

# GET /estadisticas/stock-lento?dias=60&limite=15
@estadisticas_bp.route('/stock-lento', methods=['GET'])
def listar_stock_lento():
    dias = int(request.args.get('dias', 60))
    limite = int(request.args.get('limite', 15))
    data = EstadisticasService.stock_lento(dias, limite)
    return jsonify(data), 200

# GET /estadisticas/margen-categoria?mes=YYYY-MM
@estadisticas_bp.route('/margen-categoria', methods=['GET'])
def listar_margen_por_categoria():
    mes = request.args.get('mes')
    data = EstadisticasService.margen_por_categoria(mes)
    return jsonify(data), 200

# GET /estadisticas/clientes-frecuentes?limite=10&mes=YYYY-MM
@estadisticas_bp.route('/clientes-frecuentes', methods=['GET'])
def listar_clientes_frecuentes():
    limite = int(request.args.get('limite', 10))
    mes = request.args.get('mes')
    data = EstadisticasService.clientes_frecuentes(limite, mes)
    return jsonify(data), 200

# GET /estadisticas/ticket-promedio?mes=YYYY-MM
@estadisticas_bp.route('/ticket-promedio', methods=['GET'])
def obtener_ticket_promedio():
    mes = request.args.get('mes')
    data = EstadisticasService.ticket_promedio_general(mes)
    return jsonify(data), 200

# GET /estadisticas/clientes-inactivos?dias=60&limite=15
@estadisticas_bp.route('/clientes-inactivos', methods=['GET'])
def listar_clientes_inactivos():
    dias = int(request.args.get('dias', 60))
    limite = int(request.args.get('limite', 15))
    data = EstadisticasService.clientes_inactivos(dias, limite)
    return jsonify(data), 200