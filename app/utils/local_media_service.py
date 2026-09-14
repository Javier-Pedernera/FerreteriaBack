import base64
import os
import uuid

from flask import request

# Mismo patrón que ya se usa para las listas de precios de proveedores
# (app/static/uploads/excels/...), servido por la ruta estática que Flask
# expone solo automáticamente.
MEDIA_ROOT = os.path.join('app', 'static', 'uploads')

EXTENSIONES_POR_MIME = {
    'image/jpeg': 'jpg',
    'image/jpg': 'jpg',
    'image/png': 'png',
    'image/webp': 'webp',
    'video/mp4': 'mp4',
    'video/webm': 'webm',
    'video/quicktime': 'mov',
}


class LocalMediaService:
    @staticmethod
    def guardar_base64(base64_data, carpeta):
        """
        Decodifica un data URI (ej: "data:image/jpeg;base64,....") y lo
        guarda en app/static/uploads/<carpeta>/.

        Devuelve la URL absoluta para servirlo, armada con el host de la
        request actual (así funciona igual en local y en producción, sin
        hardcodear el dominio).
        """
        try:
            header, data = base64_data.split(',', 1)
            mime = header.split(';')[0].replace('data:', '')
        except ValueError:
            raise ValueError('Formato de archivo inválido')

        extension = EXTENSIONES_POR_MIME.get(mime, 'bin')
        nombre_archivo = f"{uuid.uuid4().hex}.{extension}"

        destino = os.path.join(MEDIA_ROOT, carpeta)
        os.makedirs(destino, exist_ok=True)

        ruta_completa = os.path.join(destino, nombre_archivo)
        with open(ruta_completa, 'wb') as f:
            f.write(base64.b64decode(data))

        url_relativa = f"/static/uploads/{carpeta}/{nombre_archivo}"
        return request.host_url.rstrip('/') + url_relativa

    @staticmethod
    def eliminar(url, carpeta):
        """Borra el archivo local apuntado por `url`, si existe."""
        if not url:
            return
        nombre_archivo = url.rstrip('/').split('/')[-1]
        ruta_completa = os.path.join(MEDIA_ROOT, carpeta, nombre_archivo)
        try:
            if os.path.exists(ruta_completa):
                os.remove(ruta_completa)
        except OSError as e:
            print(f"Error al eliminar archivo local ({carpeta}): {e}")
