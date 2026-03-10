import base64
from datetime import datetime, timedelta, timezone
import json
import os
from xml.etree import ElementTree as ET
from zeep.helpers import serialize_object
from requests import Session
from zeep import Client
from zeep.transports import Transport

import ssl
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager


class TLSAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        ctx = ssl.create_default_context()
        ctx.set_ciphers("DEFAULT@SECLEVEL=1")
        kwargs["ssl_context"] = ctx
        return super().init_poolmanager(*args, **kwargs)

from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.serialization import Encoding
from cryptography.hazmat.primitives.serialization.pkcs7 import PKCS7SignatureBuilder
from cryptography.hazmat.backends import default_backend

from app.models.arca_token import ArcaToken
from app.models.empresa_fiscal_config import EmpresaFiscalConfig
from app import db
from config import Config


class ArcaService:
    """
    Servicio oficial para autenticación (WSAA) y facturación (WSFE) en ARCA.
    """

    def __init__(self, empresa: EmpresaFiscalConfig):
        self.empresa = empresa

    # =====================================================
    # TRA
    # =====================================================

    # def generar_tra(self) -> str:
    #     now = datetime.utcnow()

    #     generation_time = (now - datetime.timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%S")
    #     expiration_time = (now + datetime.timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%S")

    #     unique_id = int(now.timestamp())

    #     tra = f"""<?xml version="1.0" encoding="UTF-8"?>
    # <loginTicketRequest version="1.0">
    # <header>
    #     <uniqueId>{unique_id}</uniqueId>
    #     <generationTime>{generation_time}</generationTime>
    #     <expirationTime>{expiration_time}</expirationTime>
    # </header>
    # <service>wsfe</service>
    # </loginTicketRequest>"""

        # return tra

    # =====================================================
    # FIRMA CMS (usa certificado desde DB)
    # =====================================================

    def generar_tra(self) -> str:
        now = datetime.now(timezone.utc)  # UTC con tzinfo
        generation_time = (now - timedelta(minutes=1)).isoformat(timespec="seconds")
        expiration_time = (now + timedelta(minutes=5)).isoformat(timespec="seconds")
        unique_id = int(now.timestamp())

        tra = f"""<?xml version="1.0" encoding="UTF-8"?>
    <loginTicketRequest version="1.0">
    <header>
        <uniqueId>{unique_id}</uniqueId>
        <generationTime>{generation_time}</generationTime>
        <expirationTime>{expiration_time}</expirationTime>
    </header>
    <service>wsfe</service>
    </loginTicketRequest>"""

        return tra

    def firmar_tra(self, tra_xml: str) -> str:
        import base64
        from cryptography.hazmat.primitives.serialization import pkcs12, Encoding
        from cryptography.hazmat.primitives.serialization.pkcs7 import (
            PKCS7SignatureBuilder,
            PKCS7Options,
        )
        from cryptography.hazmat.primitives import hashes

        pfx_path = Config.ARCA_PFX_PATH
        password = Config.ARCA_PFX_PASSWORD.encode()

        with open(pfx_path, "rb") as f:
            pfx_data = f.read()

        private_key, certificate, additional_certificates = pkcs12.load_key_and_certificates(
            pfx_data,
            password
        )

        builder = PKCS7SignatureBuilder().set_data(tra_xml.encode("utf-8"))

        builder = builder.add_signer(
            certificate,
            private_key,
            hashes.SHA256()
        )

        cms = builder.sign(
            Encoding.DER,
            [PKCS7Options.Binary]
        )

        return base64.b64encode(cms).decode("utf-8")

    # =====================================================
    # LOGIN WSAA
    # =====================================================

    def login_wsaa(self):
        tra_xml = self.generar_tra()
        cms = self.firmar_tra(tra_xml)

        session = Session()
        session.mount("https://", TLSAdapter())
        transport = Transport(session=session)

        wsdl = Config.ARCA_WSAA_URL + "?WSDL"

        client = Client(wsdl=wsdl, transport=transport)

        response = client.service.loginCms(cms)

        xml = ET.fromstring(response)

        token = xml.find(".//token").text
        sign = xml.find(".//sign").text
        expiration = xml.find(".//expirationTime").text

        expiration_dt = datetime.fromisoformat(expiration)

        return token, sign, expiration_dt

    # =====================================================
    # TOKEN CACHE
    # =====================================================

    def obtener_token(self, force_new=False):
        if not force_new:
            token_db = ArcaToken.query.order_by(ArcaToken.id.desc()).first()
            if token_db and token_db.is_valid():
                return token_db.token, token_db.sign

        # Genera uno nuevo (production)
        token, sign, expiration = self.login_wsaa()  # asegúrate de que login_wsaa apunte a producción

        nuevo = ArcaToken(
            token=token,
            sign=sign,
            expiration_time=expiration
        )

        db.session.add(nuevo)
        db.session.commit()

        return token, sign
    # =====================================================
    # WSFE AUTORIZAR COMPROBANTE
    # =====================================================

    def wsfe_autorizar(self, token, sign, factura):
        from requests import Session
        from zeep import Client
        from zeep.transports import Transport
        from datetime import datetime

        # 🔴 VALIDACIÓN CLAVE
        if not factura.tipo_comprobante_id:
            raise ValueError("La factura no tiene tipo de comprobante asignado")

        if not factura.tipo_comprobante:
            raise ValueError("No se pudo cargar el tipo de comprobante")

        # print("TIPO ID:", factura.tipo_comprobante_id)
        # print("TIPO OBJ:", factura.tipo_comprobante)
        cbte_tipo = factura.tipo_comprobante.codigo_afip

        session = Session()
        session.mount("https://", TLSAdapter())
        transport = Transport(session=session)

        wsdl = Config.ARCA_WSFE_URL + "?WSDL"

        client = Client(wsdl=wsdl, transport=transport)

        auth = {
            "Token": token,
            "Sign": sign,
            "Cuit": int(self.empresa.cuit),
        }
        # print("FACTURA ID:", factura.id)
        # print("PUNTO VENTA ID:", factura.punto_venta_id)
        # print("PUNTO VENTA OBJ:", factura.punto_venta)
        if not factura.punto_venta:
            raise ValueError("La factura no tiene punto de venta asignado")

        # print("Punto de venta que se enviará a AFIP:", self.empresa.punto_venta)
        # ✅ YA NO usamos factura.arca_tipo_cbte
        ultimo_response = client.service.FECompUltimoAutorizado(
            Auth=auth,
            PtoVta=factura.punto_venta.numero,
            CbteTipo=cbte_tipo
        )

        # 🔎 Extraemos el número correctamente
        ultimo_numero = ultimo_response.CbteNro

        if ultimo_numero is None:
            ultimo_numero = 0

        numero = ultimo_numero + 1

        # 🔎 Cliente
        cliente = factura.cliente
        # print("CLIENTE:", cliente)
        # print("CLIENTE TIPO DOC:", cliente.tipo_documento)
        # print("CLIENTE COND IVA:", cliente.condicion_iva)
        if not cliente.tipo_documento:
            raise ValueError("El cliente no tiene tipo de documento asignado")
        if not cliente.condicion_iva:
            raise ValueError("El cliente no tiene condición IVA asignada")
        doc_tipo = cliente.tipo_documento.codigo_afip

        # Consumidor Final
        if doc_tipo == 99:
            doc_nro = 0
        else:
            if not cliente.cuit:
                raise ValueError("El cliente no tiene número de documento/cuit")
            doc_nro = int(cliente.cuit)
        
        # print("TIPOS QUE SE ENVÍAN:")
        # print("DocTipo:", doc_tipo, type(doc_tipo))
        # print("DocNro:", doc_nro, type(doc_nro))
        # print("CondicionIVAReceptorId:", cliente.condicion_iva, type(cliente.condicion_iva))
        
        detalle = {
            "Concepto": 1,
            "DocTipo": int(doc_tipo),
            "DocNro": int(doc_nro),
            "CbteDesde": int(numero),
            "CbteHasta": int(numero),
            "CbteFch": datetime.now().strftime("%Y%m%d"),
            "ImpTotal": float(factura.total),
            "ImpTotConc": 0,
            "ImpNeto": float(factura.total),
            "ImpOpEx": 0,
            "ImpIVA": 0,
            "ImpTrib": 0,
            "MonId": "PES",
            "MonCotiz": 1,
            "CondicionIVAReceptorId": cliente.condicion_iva.codigo_afip
        }
        # print("Datos a enviar")
        for k, v in detalle.items():
            print(k, type(v), v)
        response = client.service.FECAESolicitar(
            Auth=auth,
            FeCAEReq={
                "FeCabReq": {
                    "CantReg": 1,
                    "PtoVta": factura.punto_venta.numero,
                    "CbteTipo": cbte_tipo,  # ✅ corregido
                },
                "FeDetReq": {
                    "FECAEDetRequest": [detalle]
                },
            },
        )

        if not hasattr(response, "FeDetResp") or response.FeDetResp is None:
            response_dict = serialize_object(response)
            print("RESPUESTA COMPLETA ARCA (FeDetResp es None):")
            print(json.dumps(response_dict, indent=4))
            raise Exception("ARCA no devolvió FECAEDetResponse. Revisa la respuesta completa arriba.")

        resultado = response.FeDetResp.FECAEDetResponse[0]

        response_dict = serialize_object(response)

        # print("============= RESPUESTA COMPLETA ARCA =============")
        # print(json.dumps(response_dict, indent=4))
        # print("===================================================")

        # 1️⃣ Error general del comprobante
        if response_dict.get("Errors"):
            err = response_dict["Errors"]["Err"]
            if isinstance(err, list):
                raise Exception(f"ARCA Error {err[0]['Code']}: {err[0]['Msg']}")
            else:
                raise Exception(f"ARCA Error {err['Code']}: {err['Msg']}")

        detalle_resp = response_dict["FeDetResp"]["FECAEDetResponse"][0]
        if resultado.Resultado != "A":

            mensaje_error = "Error desconocido informado por ARCA"

            # 1️⃣ Errores (más graves)
            if hasattr(resultado, "Errors") and resultado.Errors:
                errores = resultado.Errors.Err
                if isinstance(errores, list):
                    mensaje_error = errores[0].Msg
                else:
                    mensaje_error = errores.Msg

            # 2️⃣ Observaciones (validaciones)
            elif hasattr(resultado, "Observaciones") and resultado.Observaciones:
                obs = resultado.Observaciones.Obs
                if isinstance(obs, list):
                    mensaje_error = obs[0].Msg
                else:
                    mensaje_error = obs.Msg
            # print("RESULTADO COMPLETO:")
            # print(resultado)
            raise Exception(f"ARCA rechazó el comprobante: {mensaje_error}")

        return {
            "numero": numero,
            "cae": resultado.CAE,
            "vto": datetime.strptime(
                resultado.CAEFchVto, "%Y%m%d"
            ).date(),
        }

    # =====================================================
    # MÉTODO PRINCIPAL
    # =====================================================

    def emitir_comprobante(self, factura):
        token, sign = self.obtener_token()
        return self.wsfe_autorizar(token, sign, factura)
    
    def probar_wsfe(self, cbte_tipo: int):
        from requests import Session
        from zeep import Client
        from zeep.transports import Transport

        token, sign = self.obtener_token()

        session = Session()
        session.mount("https://", TLSAdapter())
        transport = Transport(session=session)

        wsdl = Config.ARCA_WSFE_URL + "?WSDL"

        client = Client(wsdl=wsdl, transport=transport)

        auth = {
            "Token": token,
            "Sign": sign,
            "Cuit": int(self.empresa.cuit),
        }

        ultimo = client.service.FECompUltimoAutorizado(
            Auth=auth,
            PtoVta=1,
            CbteTipo=cbte_tipo
        )

        return ultimo.CbteNro or 0
    
    def listar_comprobantes_testing(self, tipo_comprobante_codigo_afip: int = 11):
        """
        Lista los comprobantes emitidos en el ambiente de testing para el punto de venta
        configurado en la empresa.
        """
        token, sign = self.obtener_token()

        from requests import Session
        from zeep import Client
        from zeep.transports import Transport

        session = Session()
        session.mount("https://", TLSAdapter())
        transport = Transport(session=session)

        # Seleccionamos el WSDL de WSFE según ambiente
        wsdl = Config.ARCA_WSFE_URL + "?WSDL"
        client = Client(wsdl=wsdl, transport=transport)

        auth = {
            "Token": token,
            "Sign": sign,
            "Cuit": int(self.empresa.cuit),
        }

        # 🔹 Consultamos el último número autorizado
        ultimo_response = client.service.FECompUltimoAutorizado(
            Auth=auth,
            PtoVta=1,
            CbteTipo=tipo_comprobante_codigo_afip
        )
        print("ultimo response", ultimo_response)
        ultimo_numero = ultimo_response.CbteNro or 0

        if ultimo_numero == 0:
            return []

        comprobantes = []

        # 🔹 Recorremos todos los números desde 1 hasta el último
        for nro in range(1, ultimo_numero + 1):
            try:
                # print("CONSULTANDO NRO:", nro)

                resp = client.service.FECompConsultar(
                    Auth=auth,
                    FeCompConsReq={
                        "CbteTipo": tipo_comprobante_codigo_afip,
                        "PtoVta": 1,
                        "CbteNro": nro
                    }
                )

                print("RESPUESTA CRUDA:", resp)

                if not resp or not resp.ResultGet:
                    print("NO TIENE ResultGet")
                    continue

                comp = resp.ResultGet

                comprobantes.append({
                    "numero": comp.CbteDesde,
                    "fecha": comp.CbteFch,
                    "importe": comp.ImpTotal,
                    "cae": comp.CodAutorizacion,
                    "vto_cae": comp.FchVto,
                    "resultado": comp.Resultado,
                    "cliente_tipo": comp.DocTipo,
                    "cliente_nro": comp.DocNro
                })

            except Exception as e:
                print("ERROR EN NRO", nro, e)
                continue

        return comprobantes    