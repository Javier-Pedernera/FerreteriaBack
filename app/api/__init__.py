from flask import Flask
from .productos_api import producto_api
from .proveedor_api import api_proveedor
# from .auth_api import auth_api
from .categoria_api import categoria_api
# from .status_api import status_api
from .unidad_medida_api import unidad_medida_bp
from .marcas_api import marca_api
from .import_templates import import_templates_bp
from .pedido_api import pedido_bp
from .detalle_pedido_api import detalle_pedido_api
from .ventas_api import ventas_api
from .clientes_api import clientes_bp
from .formas_pago_api import formas_pago_bp
from .personas_autorizadas_api import personas_bp
from .usuarios_api import usuarios_bp

def register_blueprints(app):
    
    app.register_blueprint(producto_api, url_prefix='/api')
    app.register_blueprint(api_proveedor, url_prefix='/api')
    app.register_blueprint(categoria_api, url_prefix='/api')
    app.register_blueprint(unidad_medida_bp, url_prefix='/api')
    app.register_blueprint(marca_api, url_prefix='/api')
    app.register_blueprint(import_templates_bp, url_prefix='/api')
    app.register_blueprint(pedido_bp, url_prefix="/api/pedidos-proveedor")
    app.register_blueprint(detalle_pedido_api, url_prefix="/api/pedidos-proveedor/detalle")
    app.register_blueprint(ventas_api, url_prefix='/api/ventas')
    app.register_blueprint(usuarios_bp, url_prefix='/api/usuarios')
    app.register_blueprint(clientes_bp, url_prefix='/api/clientes')
    app.register_blueprint(formas_pago_bp, url_prefix='/api/formas-pago')
    app.register_blueprint(personas_bp, url_prefix='/api/personas')
    # app.register_blueprint(auth_api, url_prefix='/api')
    # app.register_blueprint(status_api, url_prefix='/api')