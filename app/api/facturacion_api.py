from flask import Blueprint, request, jsonify

from app.models.empresa_fiscal_config import EmpresaFiscalConfig
from app.services.arca_service import ArcaService, TLSAdapter
from app.services.facturacion_service import FacturacionService
from app.models.factura import Factura
from app.services.pdf_service import generar_pdf_factura
from flask import Response, current_app

from config import Config
facturacion_api = Blueprint('facturacion_api', __name__)


# --------------------------------------------------
# CREAR FACTURA DESDE VENTAS
# --------------------------------------------------
@facturacion_api.route('/facturas', methods=['POST'])
def crear_factura():
    data = request.get_json()

    cliente_id = data.get("cliente_id")
    ventas_ids = data.get("ventas_ids")
    tipo_comprobante_id = data.get("tipo_comprobante_id")
    punto_venta_id = data.get("punto_venta_id")
    if not cliente_id or not ventas_ids:
        return jsonify({
            "message": "cliente_id y ventas_ids son obligatorios"
        }), 400

    try:
        factura = FacturacionService.crear_factura_desde_ventas(
            cliente_id,
            ventas_ids,
            punto_venta_id,
            tipo_comprobante_id,
        )

        return jsonify(factura.serialize()), 201

    except ValueError as e:
        return jsonify({"message": str(e)}), 400

    except Exception as e:
        return jsonify({
            "message": "Error al crear factura",
            "error": str(e)
        }), 500


# --------------------------------------------------
# OBTENER FACTURA POR ID
# --------------------------------------------------
@facturacion_api.route('/facturas/<int:id>', methods=['GET'])
def get_factura(id):
    factura = Factura.query.get(id)

    if factura:
        return jsonify(factura.serialize()), 200

    return jsonify({'message': 'Factura no encontrada'}), 404


# --------------------------------------------------
# LISTAR FACTURAS
# --------------------------------------------------
@facturacion_api.route('/facturas', methods=['GET'])
def get_all_facturas():
    facturas = Factura.query.order_by(Factura.id.desc()).all()
    return jsonify([f.serialize() for f in facturas]), 200


@facturacion_api.route('/facturas/<int:id>', methods=['PUT'])
def actualizar_factura(id):
    data = request.get_json()

    try:
        factura = FacturacionService.actualizar_factura(id, data)
        return jsonify(factura.serialize()), 200

    except ValueError as e:
        return jsonify({"message": str(e)}), 400

    except Exception as e:
        return jsonify({
            "message": "Error al actualizar factura",
            "error": str(e)
        }), 500
        
# --------------------------------------------------
# EMITIR FACTURA EN ARCA
# --------------------------------------------------
@facturacion_api.route('/facturas/<int:id>/emitir', methods=['POST'])
def emitir_factura(id):
    try:
        factura = FacturacionService.emitir_factura_arca(id)
        return jsonify(factura.serialize()), 200

    except ValueError as e:
        return jsonify({"message": str(e)}), 400

    except Exception as e:
        return jsonify({
            "message": "Error al emitir factura",
            "error": str(e)
        }), 500
   
   #test de arca     
@facturacion_api.route("/test-arca", methods=["GET"])
def test_arca():
    try:
        empresa = EmpresaFiscalConfig.query.filter_by(activo=True).first()

        if not empresa:
            return jsonify({"error": "No hay empresa activa"}), 400

        service = ArcaService(empresa)

        token, sign = service.obtener_token()

        return jsonify({
            "ok": True,
            "token_preview": token[:30],
            "sign_preview": sign[:30]
        })

    except Exception as e:
        return jsonify({
            "ok": False,
            "error": str(e)
        }), 500
        
# --------------------------------------------------
# TEST WSFE (probar conexión facturación)
# --------------------------------------------------
@facturacion_api.route("/test-wsfe", methods=["GET"])
def test_wsfe():
    try:
        empresa = EmpresaFiscalConfig.query.filter_by(activo=True).first()

        if not empresa:
            return jsonify({"error": "No hay empresa activa"}), 400
        tipo = request.args.get("tipo", type=int)

        if not tipo:
            return jsonify({"error": "Debe enviar ?tipo=CODIGO_AFIP"}), 400
        service = ArcaService(empresa)

        ultimo = service.probar_wsfe(tipo)

        return jsonify({
            "ok": True,
            "ultimo_autorizado": ultimo
        })

    except Exception as e:
        return jsonify({
            "ok": False,
            "error": str(e)
        }), 500
        
        
# --------------------------------------------------
# LISTAR COMPROBANTES EN TESTING (WSFE)
# --------------------------------------------------
@facturacion_api.route("/arca/comprobantes", methods=["GET"])
def listar_comprobantes_testing():
    try:
        empresa = EmpresaFiscalConfig.query.filter_by(activo=True).first()

        if not empresa:
            return jsonify({"error": "No hay empresa activa"}), 400

        # opcional: permitir pasar tipo por query param
        tipo = request.args.get("tipo", default=11, type=int)

        service = ArcaService(empresa)

        comprobantes = service.listar_comprobantes_testing(
            tipo_comprobante_codigo_afip=tipo
        )

        return jsonify({
            "ok": True,
            "ambiente": empresa.ambiente,
            "punto_venta": empresa.punto_venta,
            "tipo_cbte": tipo,
            "cantidad": len(comprobantes),
            "data": comprobantes
        }), 200

    except Exception as e:
        return jsonify({
            "ok": False,
            "error": str(e)
        }), 500        
        
        
@facturacion_api.route("/facturas/<int:id>/pdf")
def descargar_pdf(id):
    factura = Factura.query.get_or_404(id)
    # print("factura", factura)
    pdf = generar_pdf_factura(factura)

    return Response(
        pdf,
        mimetype="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=factura_{factura.numero}.pdf"
        }
    )
    
@facturacion_api.route("/arca/puntos-venta-monotributo", methods=["GET"])
def listar_puntos_venta_monotributo():
    try:
        empresa = EmpresaFiscalConfig.query.filter_by(activo=True).first()
        if not empresa:
            return jsonify({"error": "No hay empresa activa"}), 400

        service = ArcaService(empresa)
        token, sign = service.obtener_token(force_new=True)

        from zeep import Client
        from zeep.transports import Transport
        from requests import Session

        session = Session()
        session.mount("https://", TLSAdapter())
        transport = Transport(session=session)

        wsdl = Config.ARCA_WSFE_URL + "?WSDL"
        client = Client(wsdl=wsdl, transport=transport)

        auth = {
            "Token": token,
            "Sign": sign,
            "Cuit": int(empresa.cuit),
        }

        # 🔹 Llamada al WSFE para listar todos los puntos de venta habilitados
        response = client.service.FEParamGetPtosVenta(Auth=auth)

        puntos = []
        ptos = getattr(response, "PtoVta", [])
        if not isinstance(ptos, list):
            ptos = [ptos]

        for pto in ptos:
            puntos.append({
                "numero": pto.Nro,
                "nombre": getattr(pto, "Nombre", None),
                "tipo": getattr(pto, "Tipo", None),
                "habilitado": getattr(pto, "Bloqueado", 0) == 0
            })

        return jsonify({"ok": True, "puntos_venta": puntos})

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
    
    
@facturacion_api.route("/arca/comprobante/<int:cbte_tipo>/<int:pto_venta>/<int:numero>", methods=["GET"])
def consultar_comprobante_arca(cbte_tipo, pto_venta, numero):
    """
    Consulta un comprobante específico en ARCA (producción o testing según configuración del punto de venta).
    Parámetros:
        cbte_tipo: Código AFIP del tipo de comprobante (ej: 11 para factura A)
        pto_venta: Número del punto de venta
        numero: Número del comprobante
    """
    try:
        empresa = EmpresaFiscalConfig.query.filter_by(activo=True).first()
        if not empresa:
            return jsonify({"error": "No hay empresa activa"}), 400

        service = ArcaService(empresa)
        token, sign = service.obtener_token(force_new=True)  # token de producción

        from zeep import Client, Transport, helpers
        from requests import Session

        session = Session()
        session.mount("https://", TLSAdapter())
        transport = Transport(session=session)
        wsdl = Config.ARCA_WSFE_URL + "?WSDL"
        client = Client(wsdl=wsdl, transport=transport)

        auth = {
            "Token": token,
            "Sign": sign,
            "Cuit": int(empresa.cuit),
        }

        # 🔹 Llamada oficial a ARCA para consultar el comprobante
        response = client.service.FECompConsultar(
            Auth=auth,
            FeCompConsReq={
                "CbteTipo": cbte_tipo,
                "PtoVta": pto_venta,
                "CbteNro": numero
            }
        )

        # Serializamos la respuesta
        data = helpers.serialize_object(response)

        if not hasattr(response, "ResultGet") or response.ResultGet is None:
            return jsonify({
                "ok": False,
                "error": "ARCA no devolvió información del comprobante"
            }), 404

        comp = response.ResultGet

        resultado = {
            "numero": comp.CbteDesde,
            "fecha": comp.CbteFch,
            "importe": comp.ImpTotal,
            "cae": comp.CodAutorizacion,
            "vto_cae": comp.FchVto,
            "resultado": comp.Resultado,
            "cliente_tipo": comp.DocTipo,
            "cliente_nro": comp.DocNro,
            "concepto": comp.Concepto
        }

        return jsonify({
            "ok": True,
            "comprobante": resultado
        })

    except Exception as e:
        return jsonify({
            "ok": False,
            "error": str(e)
        }), 500
        
@facturacion_api.route("/arca/cae/<string:cae>", methods=["GET"])
def consultar_por_cae(cae):
    try:

        empresa = EmpresaFiscalConfig.query.filter_by(activo=True).first()
        if not empresa:
            return jsonify({"error": "No hay empresa activa"}), 400

        # 🔹 buscar factura en tu sistema
        factura = Factura.query.filter_by(arca_cae=cae).first()

        if not factura:
            return jsonify({
                "ok": False,
                "error": "No existe una factura con ese CAE en el sistema"
            }), 404

        service = ArcaService(empresa)
        token, sign = service.obtener_token(force_new=True)

        from zeep import Client
        from zeep.transports import Transport
        from requests import Session

        session = Session()
        session.mount("https://", TLSAdapter())
        transport = Transport(session=session)

        wsdl = Config.ARCA_WSFE_URL + "?WSDL"
        client = Client(wsdl=wsdl, transport=transport)

        auth = {
            "Token": token,
            "Sign": sign,
            "Cuit": int(empresa.cuit),
        }

        response = client.service.FECompConsultar(
            Auth=auth,
            FeCompConsReq={
                "CbteTipo": factura.tipo_comprobante.codigo_afip,
                "PtoVta": factura.punto_venta_emitido,
                "CbteNro": factura.arca_numero_cbte
            }
        )

        if not response.ResultGet:
            return jsonify({
                "ok": False,
                "error": "ARCA no devolvió datos"
            })

        comp = response.ResultGet

        return jsonify({
            "ok": True,
            "arca": {
                "cae": comp.CodAutorizacion,
                "fecha": comp.CbteFch,
                "importe": comp.ImpTotal,
                "resultado": comp.Resultado,
                "vto_cae": comp.FchVto,
                "cliente_tipo": comp.DocTipo,
                "cliente_nro": comp.DocNro
            },
            "sistema": factura.serialize()
        })

    except Exception as e:
        return jsonify({
            "ok": False,
            "error": str(e)
        }), 500