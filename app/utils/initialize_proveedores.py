from app.models.proveedor import Proveedor
from app import db

def initialize_proveedores():
    proveedores_default = [
        {
            "nombre": "Rodolfo Berger",
            "codigo_proveedor": "BER",
            "sitio_web": "https://www.rodolfoberger.com.ar/",
            "direccion": "Av. Belardinelli 3277, B° San Fernando, Córdoba",
            "porcentaje_ganancia": 50,
            "precio_con_iva": True,
            "descripcion": "Proveedor mayorista de herramientas",
            "status_id": 1
        },
        {
            "nombre": "LEKONS",
            "codigo_proveedor": "LEK",
            "sitio_web": "https://www.lekons.com.ar/",
            "direccion": "Bv. los Alemanes 3312 - Los Boulevares / Córdoba Capital",
            "porcentaje_ganancia": 0, #segun sugerido
            "precio_con_iva": False,
            "descripcion": "Distribuidor de artículos ferreteros y eléctricos",
            "status_id": 1
        },
        {
            "nombre": "WALTER",
            "codigo_proveedor": "WAL",
            "sitio_web": "",
            "direccion": "",
            "porcentaje_ganancia": 50,
            "precio_con_iva": True,
            "descripcion": "Proveedor de herramientas y artículos importados",
            "status_id": 1
        },
        {
            "nombre": "MACONS",
            "codigo_proveedor": "MAC",
            "sitio_web": "https://macons.com.ar/",
            "direccion": "Gral. Manuel Savio 5740",
            "porcentaje_ganancia": 60,
            "precio_con_iva": True,
            "descripcion": "Distribuidora mayorista de ferretería",
            "status_id": 1
        },
        {
            "nombre": "BARTOLACCI",
            "codigo_proveedor": "BAR",
            "sitio_web": "https://www.facebook.com/bartolacci.distribuidora/",
            "direccion": "",
            "porcentaje_ganancia": 0,
            "precio_con_iva": True,
            "descripcion": "Proveedor de herramientas y artículos importados",
            "status_id": 1
        },
        {
            "nombre": "SUSI",
            "codigo_proveedor": "SUS",
            "sitio_web": "",
            "direccion": "",
            "porcentaje_ganancia": 0,
            "precio_con_iva": True,
            "descripcion": "Distribuidora de productos eléctricos",
            "status_id": 1
        },
        {
            "nombre": "MOTA Y TOTAL",
            "codigo_proveedor": "MOT",
            "sitio_web": "https://www.mota.com.ar/Puntos_ARGENTINA.htm",
            "direccion": "",
            "porcentaje_ganancia": 50,
            "precio_con_iva": True,
            "descripcion": "Distribuidora de productos eléctricos",
            "status_id": 1
        },
        {
            "nombre": "IRELAND",
            "codigo_proveedor": "IRE",
            "sitio_web": "",
            "direccion": "",
            "porcentaje_ganancia": 82,
            "precio_con_iva": True,
            "descripcion": "Distribuidora de pinturas",
            "status_id": 1
        },
        {
            "nombre": "DILMAS",
            "codigo_proveedor": "DIL",
            "sitio_web": "",
            "direccion": "",
            "porcentaje_ganancia": 50,
            "precio_con_iva": True,
            "descripcion": "Distribuidora de herramientas",
            "status_id": 1
        },
        {
            "nombre": "POXIPOL",
            "codigo_proveedor": "POX",
            "sitio_web": "https://www.poxipol.com.ar/",
            "direccion": "",
            "porcentaje_ganancia": 50,
            "precio_con_iva": True,
            "descripcion": "Distribuidora PEGAMENTOS",
            "status_id": 1
        },
        {
            "nombre": "LUMAC",
            "codigo_proveedor": "LUM",
            "sitio_web": "http://dist-lumac.com/",
            "direccion": "",
            "porcentaje_ganancia": 45,
            "precio_con_iva": True,
            "descripcion": "Distribuidora de PEGAMENTOS",
            "status_id": 1
        },
        {
            "nombre": "VRONCE",
            "codigo_proveedor": "VRO",
            "sitio_web": "http://dist-lumac.com/",
            "direccion": "",
            "porcentaje_ganancia": 45,
            "precio_con_iva": True,
            "descripcion": "Distribuidora de CERRADURAS",
            "status_id": 1
        }
    ]

    for prov in proveedores_default:
        if not Proveedor.query.filter_by(codigo_proveedor=prov['codigo_proveedor']).first():
            nuevo = Proveedor(**prov)
            db.session.add(nuevo)

    db.session.commit()
