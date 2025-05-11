from app import db
from app.models.producto import Producto
from sqlalchemy import or_
from app.utils.cloudinary_service import CloudinaryService

class ProductoService:

    @staticmethod
    def obtener_todos():
        return Producto.query.all()

    @staticmethod
    def obtener_por_id(producto_id):
        return Producto.query.get_or_404(producto_id)

    @staticmethod
    def crear(data):
        # Construir el código interno desde el código del proveedor y un string adicional
        codigo_proveedor = data['codigo_proveedor']
        codigo_str = data['codigo_str']
        cod_interno = f"{codigo_proveedor}-{codigo_str}"

        producto = Producto(
            cod_interno=cod_interno,
            cod_proveedor=codigo_proveedor,
            nombre=data['nombre'],
            nombre_corto=data.get('nombre_corto'),
            descripcion=data.get('descripcion'),
            precio_ars=data['precio_ars'],
            precio_usd=data.get('precio_usd'),
            porcentaje_ganancia=data.get('porcentaje_ganancia'),
            disponibles=data.get('disponibles', 0),
            proveedor_id=data['proveedor_id'],
            categoria_id=data.get('categoria_id'),
            status_id=data['status_id'],
            unidad_medida_id=data['unidad_medida_id'],
            marca_id=data.get('marca_id'),
            ubicacion_local=data.get('ubicacion_local')
        )

        producto.precio_final = producto.calcular_precio_final()

        db.session.add(producto)
        db.session.commit()

        # Manejar imágenes base64 si existen
        imagenes_base64 = data.get('imagenes_base64', [])
        imagen_portada_index = data.get('imagen_portada_index', 0) 

        for i, base64_imagen in enumerate(imagenes_base64[:3]): 
            public_id = f"productos/{cod_interno}-{i+1}"
            es_portada = i == imagen_portada_index
            upload_result = CloudinaryService.subir_imagen(base64_imagen, public_id)
            if upload_result and 'secure_url' in upload_result:
                CloudinaryService.guardar_url_imagen(producto.id, upload_result['secure_url'], es_portada)

        return producto

    @staticmethod
    def actualizar(producto_id, data):
        producto = Producto.query.get_or_404(producto_id)

        if 'cod_interno' in data and data['cod_interno'] != producto.cod_interno:
            raise ValueError("El código interno no se puede modificar.")

        campos_actualizables = ['cod_proveedor', 'nombre', 'nombre_corto', 'descripcion',
                                'precio_ars', 'precio_usd', 'precio_sugerido', 'porcentaje_ganancia', 'disponibles',
                                'proveedor_id', 'categoria_id', 'status_id', 'unidad_medida_id',
                                'marca_id', 'ubicacion_local', 'porcentaje_ganancia_personalizado']

        for campo in campos_actualizables:
            if campo in data:
                setattr(producto, campo, data[campo])

        producto.precio_final = producto.calcular_precio_final()
        db.session.commit()
        
        # Manejar la subida de nuevas imágenes
        if 'nuevas_imagenes_base64' in data and isinstance(data['nuevas_imagenes_base64'], list):
            # Primero eliminamos las imágenes existentes (tanto en Cloudinary como en la base de datos)
            CloudinaryService.eliminar_imagenes_producto(producto_id)
            # Luego subimos las nuevas imágenes
            for i, base64_imagen in enumerate(data['nuevas_imagenes_base64'][:3]):
                public_id = f"productos/{producto.cod_interno}-{i+1}"
                es_portada = i == 0
                upload_result = CloudinaryService.subir_imagen(base64_imagen, public_id)
                if upload_result and 'secure_url' in upload_result:
                    CloudinaryService.guardar_url_imagen(producto.id, upload_result['secure_url'], es_portada)

        return producto

    @staticmethod
    def eliminar(producto_id):
        producto = Producto.query.get_or_404(producto_id)
        db.session.delete(producto)
        db.session.commit()
        return True
    
    @staticmethod
    def buscar_con_filtros(page=1, limit=20, query=None, categoria_id=None, proveedor_id=None, marca_id=None, status_id=None):
        q = Producto.query

        if query:
            q = q.filter(or_(
                Producto.nombre.ilike(f"%{query}%"),
                Producto.cod_interno.ilike(f"%{query}%"),
                Producto.cod_proveedor.ilike(f"%{query}%")
            ))

        if categoria_id:
            q = q.filter_by(categoria_id=categoria_id)
        if proveedor_id:
            q = q.filter_by(proveedor_id=proveedor_id)
        if marca_id:
            q = q.filter_by(marca_id=marca_id)
        if status_id:
            q = q.filter_by(status_id=status_id)

        total = q.count()
        productos = q.order_by(Producto.nombre).offset((page - 1) * limit).limit(limit).all()

        return productos, total