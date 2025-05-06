from app import db
from app.models.marca import Marca

class MarcaService:

    @staticmethod
    def get_all_marcas():
        """
        Obtiene todas las marcas disponibles.
        """
        return Marca.query.all()

    @staticmethod
    def get_marca_by_id(marca_id):
        """
        Obtiene una marca por su ID.
        """
        return Marca.query.get(marca_id)

    @staticmethod
    def create_marca(data):
        """
        Crea una nueva marca con los datos proporcionados.
        """
        new_marca = Marca(
            nombre=data['nombre'],
            descripcion=data.get('descripcion', ''),
            pais_origen=data.get('pais_origen', ''),
            logo_url=data.get('logo_url', ''),
        )
        db.session.add(new_marca)
        db.session.commit()
        return new_marca

    @staticmethod
    def update_marca(marca_id, data):
        """
        Actualiza una marca existente.
        """
        marca = Marca.query.get(marca_id)
        if marca:
            marca.nombre = data.get('nombre', marca.nombre)
            marca.descripcion = data.get('descripcion', marca.descripcion)
            marca.pais_origen = data.get('pais_origen', marca.pais_origen)
            marca.logo_url = data.get('logo_url', marca.logo_url)
            db.session.commit()
            return marca
        return None

    @staticmethod
    def delete_marca(marca_id):
        """
        Elimina una marca.
        """
        marca = Marca.query.get(marca_id)
        if marca:
            db.session.delete(marca)
            db.session.commit()
            return True
        return False

    @staticmethod
    def cargar_marcas():
        """
        Carga marcas conocidas en la base de datos si no existen.
        """
        marcas_conocidas = [
            {'nombre': 'Aldo', 'descripcion': 'Herramientas y productos de construcción', 'pais_origen': 'Argentina'},
            {'nombre': 'Güero', 'descripcion': 'Herramientas y productos de ferretería', 'pais_origen': 'Argentina'},
            {'nombre': 'Truper', 'descripcion': 'Herramientas y equipo de ferretería', 'pais_origen': 'México'},
            {'nombre': 'Stanley', 'descripcion': 'Herramientas manuales', 'pais_origen': 'Estados Unidos'},
            {'nombre': 'Black+Decker', 'descripcion': 'Herramientas eléctricas', 'pais_origen': 'Estados Unidos'},
            {'nombre': 'Makita', 'descripcion': 'Herramientas eléctricas', 'pais_origen': 'Japón'},
            {'nombre': 'Bosch', 'descripcion': 'Herramientas eléctricas y accesorios', 'pais_origen': 'Alemania'},
            {'nombre': 'Vonder', 'descripcion': 'Herramientas y equipamiento industrial', 'pais_origen': 'Brasil'},
            {'nombre': 'Cremasco', 'descripcion': 'Herramientas y elementos de ferretería', 'pais_origen': 'Argentina'},
            {'nombre': 'Sika', 'descripcion': 'Productos químicos para construcción', 'pais_origen': 'Suiza'}
        ]

        for marca in marcas_conocidas:
            if not Marca.query.filter_by(nombre=marca['nombre']).first():
                new_marca = Marca(**marca)
                db.session.add(new_marca)

        db.session.commit()
