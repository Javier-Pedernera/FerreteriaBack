from app import db
from app.models import EmpresaFiscalConfig


class EmpresaFiscalService:

    @staticmethod
    def get_empresa_activa():
        empresa = EmpresaFiscalConfig.query.filter_by(activo=True).first()
        if not empresa:
            raise ValueError("No hay ninguna empresa fiscal activa configurada")
        return empresa

    @staticmethod
    def get_all():
        return EmpresaFiscalConfig.query.all()

    @staticmethod
    def get_by_id(empresa_id):
        empresa = EmpresaFiscalConfig.query.get(empresa_id)
        if not empresa:
            raise ValueError("Empresa fiscal no encontrada")
        return empresa

    @staticmethod
    def create(data):
        # Si la nueva empresa viene como activa, desactivamos otras
        if data.get("activo", True):
            db.session.query(EmpresaFiscalConfig).filter_by(activo=True).update({"activo": False})

        empresa = EmpresaFiscalConfig(
            razon_social=data["razon_social"],
            nombre_fantasia=data.get("nombre_fantasia"),
            cuit=data["cuit"],
            domicilio=data.get("domicilio"),
            ingresos_brutos=data.get("ingresos_brutos"),
            inicio_actividades=data.get("inicio_actividades"),
            condicion_iva_id=data["condicion_iva_id"],
            cert_path=data["cert_path"],
            pfx_password=data["pfx_password"],  # ✅ NUEVO
            ambiente=data.get("ambiente", "testing"),
            activo=data.get("activo", True),
            logo_url=data.get("logo_url")
        )

        db.session.add(empresa)
        db.session.commit()
        return empresa

    @staticmethod
    def update(empresa_id, data):
        empresa = EmpresaFiscalConfig.query.get(empresa_id)
        if not empresa:
            raise ValueError("Empresa fiscal no encontrada")

        # Si la actualización activa esta empresa, desactivar las demás
        if data.get("activo") is True:
            db.session.query(EmpresaFiscalConfig).filter(
                EmpresaFiscalConfig.id != empresa_id,
                EmpresaFiscalConfig.activo == True
            ).update({"activo": False})

        empresa.razon_social = data.get("razon_social", empresa.razon_social)
        empresa.nombre_fantasia = data.get("nombre_fantasia", empresa.nombre_fantasia)
        empresa.cuit = data.get("cuit", empresa.cuit)
        empresa.domicilio = data.get("domicilio", empresa.domicilio)
        empresa.ingresos_brutos = data.get("ingresos_brutos", empresa.ingresos_brutos)
        empresa.inicio_actividades = data.get("inicio_actividades", empresa.inicio_actividades)
        empresa.condicion_iva_id = data.get("condicion_iva_id", empresa.condicion_iva_id)
        empresa.cert_path = data.get("cert_path", empresa.cert_path)
        empresa.pfx_password = data.get("pfx_password", empresa.pfx_password)  # ✅ NUEVO
        empresa.ambiente = data.get("ambiente", empresa.ambiente)
        empresa.activo = data.get("activo", empresa.activo)
        empresa.logo_url = data.get("logo_url", empresa.logo_url)

        db.session.commit()
        return empresa