import cloudinary.uploader
from config import Config
from app import db
from app.models.imagen_producto import ImagenProducto  # Asumo que tienes este modelo

class CloudinaryService:
    @staticmethod
    def subir_imagen(base64_imagen, public_id):
        """
        Sube una imagen a Cloudinary.

        Args:
            base64_imagen (str): La cadena Base64 de la imagen.
            public_id (str): El nombre público que se le dará a la imagen en Cloudinary.
            es_portada (bool): Indica si la imagen es la portada del producto.

        Returns:
            dict: La respuesta de Cloudinary después de la subida, o None si hay error.
        """
        try:
            upload_result = cloudinary.uploader.upload(
                base64_imagen,
                public_id=public_id,
                folder="productos",  # Guardar en la carpeta 'productos'
                transformation=[
                    {'width': 800, 'height': 800, 'crop': 'limit'},  # Ejemplo de redimensionamiento
                    {'quality': 'auto', 'format': 'webp'}         # Ejemplo de optimización
                ]
            )
            return upload_result
        except Exception as e:
            print(f"Error al subir la imagen a Cloudinary: {e}")
            return None

    @staticmethod
    def eliminar_imagen(public_id):
        """
        Elimina una imagen de Cloudinary.

        Args:
            public_id (str): El nombre público de la imagen en Cloudinary.

        Returns:
            dict: La respuesta de Cloudinary después de la eliminación, o None si hay error.
        """
        try:
            delete_result = cloudinary.uploader.destroy(public_id)
            return delete_result
        except Exception as e:
            print(f"Error al eliminar la imagen de Cloudinary: {e}")
            return None

    @staticmethod
    def guardar_url_imagen(producto_id, cloudinary_url, es_portada=False):
        """
        Guarda la URL de la imagen en la tabla de imágenes del producto.

        Args:
            producto_id (int): El ID del producto asociado a la imagen.
            cloudinary_url (str): La URL de la imagen en Cloudinary.
            es_portada (bool): Indica si la imagen es la portada del producto.
        """
        imagen = ImagenProducto(producto_id=producto_id, url=cloudinary_url, es_portada=es_portada)
        db.session.add(imagen)
        db.session.commit()
        return imagen

    @staticmethod
    def obtener_urls_imagenes_producto(producto_id):
        """
        Obtiene todas las URLs de las imágenes asociadas a un producto.

        Args:
            producto_id (int): El ID del producto.

        Returns:
            list: Una lista de diccionarios con la URL y si es portada.
        """
        imagenes = ImagenProducto.query.filter_by(producto_id=producto_id).all()
        return [{'url': imagen.url, 'es_portada': imagen.es_portada} for imagen in imagenes]

    @staticmethod
    def eliminar_imagenes_producto(producto_id):
        """
        Elimina todas las imágenes de Cloudinary asociadas a un producto y sus registros en la base de datos.

        Args:
            producto_id (int): El ID del producto.
        """
        imagenes = ImagenProducto.query.filter_by(producto_id=producto_id).all()
        for imagen in imagenes:
            # Extraer el public_id de la URL si es necesario, o asumimos que lo tenemos guardado
            # Una forma sencilla si el public_id se generó como productos_codigo-numero
            public_id = f"productos/{imagen.url.split('/')[-1].split('.')[0]}"
            CloudinaryService.eliminar_imagen(public_id)
            db.session.delete(imagen)
        db.session.commit()