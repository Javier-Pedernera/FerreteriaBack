from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from app.extensions import bcrypt, jwt
from flask_migrate import Migrate
import logging
from flask_cors import CORS
from config import Config
# Inicializamos SQLAlchemy
db = SQLAlchemy()
migrate = Migrate()
def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')
    Config.configure_cloudinary()
    # Configurar logging para que se muestren todos los logs de Flask
    logging.basicConfig(level=logging.DEBUG)
    app.logger.setLevel(logging.DEBUG)

    # Inicializamos la base de datos
    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    CORS(app, resources={r"*": {"origins": "*"}})
    # Importar y registrar blueprints después de que la app esté configurada
    from .api import register_blueprints
    register_blueprints(app)

    def _seed(nombre, fn):
        """
        Corre un seeder sin tirar abajo toda la app si falla (ej. porque
        todavia falta aplicar una migracion que agrega una columna que el
        seeder necesita). Antes, si un seeder fallaba aca, ni siquiera se
        podia correr 'flask db upgrade' para arreglarlo, porque ese comando
        tambien pasa por create_app().
        """
        try:
            fn()
        except Exception as e:
            db.session.rollback()
            app.logger.warning(f"Seeder '{nombre}' fallo (se ignora, probablemente falta una migracion): {e}")

    with app.app_context():
        db.create_all()
        from app.utils.statusLoader import initialize_statuses
        _seed('statuses', initialize_statuses)
        from app.utils.categoriaLoader import initialize_categorias
        _seed('categorias', initialize_categorias)
        from app.utils.unidadMedidaLoader import initialize_unidades_medida
        _seed('unidades_medida', initialize_unidades_medida)
        from app.utils.initialize_proveedores import initialize_proveedores
        _seed('proveedores', initialize_proveedores)
        from app.utils.formasPagoLoader import initialize_formas_pago
        _seed('formas_pago', initialize_formas_pago)
        from app.utils.condiciones_iva_loader import initialize_condiciones_iva
        _seed('condiciones_iva', initialize_condiciones_iva)
        from app.utils.initialize_tipos_comprobante import initialize_tipos_comprobante
        _seed('tipos_comprobante', initialize_tipos_comprobante)
        from app.utils.initialize_tipos_documento import initialize_tipos_documento
        _seed('tipos_documento', initialize_tipos_documento)
    return app
