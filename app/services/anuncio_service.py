from app import db
from app.models.anuncio import Anuncio, POSICIONES_ANUNCIO, TIPOS_ANUNCIO
from app.utils.local_media_service import LocalMediaService

CARPETA_ANUNCIOS = 'anuncios'


class AnuncioService:

    @staticmethod
    def _validar_tipo_y_posicion(data):
        tipo = data.get('tipo')
        posicion = data.get('posicion', 'carrusel')
        if tipo not in TIPOS_ANUNCIO:
            raise ValueError(f"tipo inválido. Valores permitidos: {TIPOS_ANUNCIO}")
        if posicion not in POSICIONES_ANUNCIO:
            raise ValueError(f"posicion inválida. Valores permitidos: {POSICIONES_ANUNCIO}")
        return tipo, posicion

    @staticmethod
    def get_all(filtros=None):
        filtros = filtros or {}
        query = Anuncio.query
        if filtros.get('posicion'):
            query = query.filter(Anuncio.posicion == filtros['posicion'])
        return query.order_by(Anuncio.posicion.asc(), Anuncio.orden.asc()).all()

    @staticmethod
    def get_by_id(anuncio_id):
        return Anuncio.query.get(anuncio_id)

    @staticmethod
    def get_publicos():
        """
        Forma en que la pantalla del TV consume el contenido: agrupado por
        posición, listo para armar la secuencia intro -> carrusel -> outro.
        """
        activos = Anuncio.query.filter(Anuncio.activo.is_(True)).order_by(Anuncio.orden.asc()).all()

        intro = next((a for a in activos if a.posicion == 'intro'), None)
        outro = next((a for a in activos if a.posicion == 'outro'), None)
        carrusel = [a for a in activos if a.posicion == 'carrusel']

        return {
            'intro': intro.serialize_publico() if intro else None,
            'carrusel': [a.serialize_publico() for a in carrusel],
            'outro': outro.serialize_publico() if outro else None,
        }

    @staticmethod
    def _desactivar_otros_de_la_misma_posicion(posicion, excluir_id=None):
        """
        Para intro/outro solo debe quedar un anuncio activo a la vez. Al
        reemplazar el logo de apertura/cierre, borramos también el archivo
        anterior del disco para no acumular archivos huérfanos.
        """
        query = Anuncio.query.filter(Anuncio.posicion == posicion, Anuncio.activo.is_(True))
        if excluir_id is not None:
            query = query.filter(Anuncio.id != excluir_id)
        for otro in query.all():
            otro.activo = False
            LocalMediaService.eliminar(otro.url, carpeta=CARPETA_ANUNCIOS)

    @staticmethod
    def create(data):
        tipo, posicion = AnuncioService._validar_tipo_y_posicion(data)

        if not data.get('url') and not data.get('archivo_base64'):
            raise ValueError("Debe enviarse 'url' o 'archivo_base64'")

        url = data.get('url')
        if data.get('archivo_base64'):
            url = LocalMediaService.guardar_base64(data['archivo_base64'], carpeta=CARPETA_ANUNCIOS)

        activo = data.get('activo', True)

        # Si va a quedar activo en intro/outro, el que estaba antes pasa a inactivo.
        if activo and posicion in ('intro', 'outro'):
            AnuncioService._desactivar_otros_de_la_misma_posicion(posicion)

        anuncio = Anuncio(
            posicion=posicion,
            tipo=tipo,
            url=url,
            titulo=data.get('titulo'),
            duracion_ms=data.get('duracion_ms') if tipo == 'imagen' else None,
            orden=data.get('orden', 0),
            activo=activo,
        )
        db.session.add(anuncio)
        db.session.commit()
        return anuncio

    @staticmethod
    def update(anuncio_id, data):
        anuncio = Anuncio.query.get(anuncio_id)
        if not anuncio:
            return None

        if 'tipo' in data and data['tipo'] not in TIPOS_ANUNCIO:
            raise ValueError(f"tipo inválido. Valores permitidos: {TIPOS_ANUNCIO}")
        if 'posicion' in data and data['posicion'] not in POSICIONES_ANUNCIO:
            raise ValueError(f"posicion inválida. Valores permitidos: {POSICIONES_ANUNCIO}")

        posicion = data.get('posicion', anuncio.posicion)
        tipo = data.get('tipo', anuncio.tipo)

        if data.get('archivo_base64'):
            url_anterior = anuncio.url
            anuncio.url = LocalMediaService.guardar_base64(data['archivo_base64'], carpeta=CARPETA_ANUNCIOS)
            LocalMediaService.eliminar(url_anterior, carpeta=CARPETA_ANUNCIOS)
        elif 'url' in data:
            anuncio.url = data['url']

        anuncio.posicion = posicion
        anuncio.tipo = tipo
        anuncio.titulo = data.get('titulo', anuncio.titulo)
        anuncio.orden = data.get('orden', anuncio.orden)
        if 'duracion_ms' in data:
            anuncio.duracion_ms = data['duracion_ms'] if tipo == 'imagen' else None

        nuevo_activo = data.get('activo', anuncio.activo)
        if nuevo_activo and posicion in ('intro', 'outro'):
            AnuncioService._desactivar_otros_de_la_misma_posicion(posicion, excluir_id=anuncio.id)
        anuncio.activo = nuevo_activo

        db.session.commit()
        return anuncio

    @staticmethod
    def reordenar(orden_ids):
        """orden_ids: lista de ids de anuncios de 'carrusel', en el orden deseado."""
        for indice, anuncio_id in enumerate(orden_ids):
            Anuncio.query.filter(Anuncio.id == anuncio_id).update({'orden': indice})
        db.session.commit()

    @staticmethod
    def delete(anuncio_id):
        anuncio = Anuncio.query.get(anuncio_id)
        if not anuncio:
            return False
        LocalMediaService.eliminar(anuncio.url, carpeta=CARPETA_ANUNCIOS)
        db.session.delete(anuncio)
        db.session.commit()
        return True
