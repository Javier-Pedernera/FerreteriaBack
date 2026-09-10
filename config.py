from datetime import timedelta
import os
from dotenv import load_dotenv
import cloudinary

load_dotenv()
# print(os.getenv("DATABASE_URL"))
class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES", 10800)))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv('SECRET_KEY')

    CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
    CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
    CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")
    
    MOVIMIENTOS_CLIENTE_ENABLED = os.getenv("MOVIMIENTOS_CLIENTE_ENABLED", "false").lower() == "true"
    
# ARCA (ex AFIP)
    # Estas URLs son fijas de AFIP (no dependen de la empresa), quedan
    # siempre disponibles para que ArcaService elija según
    # EmpresaFiscalConfig.ambiente en vez de depender de una sola variable
    # de entorno global del proceso.
    ARCA_WSAA_URL_PROD = "https://wsaa.afip.gov.ar/ws/services/LoginCms"
    ARCA_WSFE_URL_PROD = "https://servicios1.afip.gov.ar/wsfev1/service.asmx"
    ARCA_WSAA_URL_TEST = "https://wsaahomo.afip.gov.ar/ws/services/LoginCms"
    ARCA_WSFE_URL_TEST = "https://wswhomo.afip.gov.ar/wsfev1/service.asmx"

    # Certificados de fallback, siempre disponibles por ambiente (no
    # condicionados a ARCA_ENV), para que si una EmpresaFiscalConfig no trae
    # su propio cert_path/pfx_password, el fallback coincida con SU
    # ambiente y no con el ARCA_ENV del proceso.
    ARCA_PFX_PATH_PROD = os.getenv("ARCA_PFX_PROD")
    ARCA_PFX_PASSWORD_PROD = os.getenv("ARCA_PFX_PROD_PASSWORD")
    ARCA_PFX_PATH_TEST = os.getenv("ARCA_PFX_TEST")
    ARCA_PFX_PASSWORD_TEST = os.getenv("ARCA_PFX_TEST_PASSWORD")

    ARCA_ENV = os.getenv("ARCA_ENV", "test")
    # print("Arca en el .env", ARCA_ENV)
    if ARCA_ENV == "prod":
        # Usados como fallback si una EmpresaFiscalConfig no trae su propio
        # cert_path/pfx_password cargado.
        ARCA_PFX_PATH = os.getenv("ARCA_PFX_PROD")
        ARCA_PFX_PASSWORD = os.getenv("ARCA_PFX_PROD_PASSWORD")
        ARCA_WSAA_URL = ARCA_WSAA_URL_PROD
        ARCA_WSFE_URL = ARCA_WSFE_URL_PROD
    else:
        ARCA_PFX_PATH = os.getenv("ARCA_PFX_TEST")
        ARCA_PFX_PASSWORD = os.getenv("ARCA_PFX_TEST_PASSWORD")
        ARCA_WSAA_URL = ARCA_WSAA_URL_TEST
        ARCA_WSFE_URL = ARCA_WSFE_URL_TEST

    ARCA_CUIT = os.getenv("ARCA_CUIT")

    @staticmethod
    def configure_cloudinary():
        cloudinary.config(
            cloud_name=Config.CLOUDINARY_CLOUD_NAME,
            api_key=Config.CLOUDINARY_API_KEY,
            api_secret=Config.CLOUDINARY_API_SECRET
        )