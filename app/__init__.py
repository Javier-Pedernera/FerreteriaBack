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

    with app.app_context():
        db.create_all()
        from app.utils.statusLoader import initialize_statuses
        initialize_statuses()
        from app.utils.categoriaLoader import initialize_categorias
        initialize_categorias()
        from app.utils.unidadMedidaLoader import initialize_unidades_medida
        initialize_unidades_medida()
        from app.utils.initialize_proveedores import initialize_proveedores
        initialize_proveedores()
        from app.utils.formasPagoLoader import initialize_formas_pago
        initialize_formas_pago()
    return app
