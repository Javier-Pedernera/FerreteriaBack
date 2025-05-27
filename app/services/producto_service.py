from app import db
from app.models.producto import Producto
from sqlalchemy import or_
from app.models.proveedor import Proveedor
from app.utils.cloudinary_service import CloudinaryService

class ProductoService:

    @staticmethod
    def obtener_todos():
        return Producto.query.all()

    @staticmethod
    def crear(data):
        proveedor = Proveedor.query.get(data['proveedor_id'])
        if not proveedor:
            raise ValueError("Proveedor no encontrado")

        codigo_proveedor = proveedor.codigo_proveedor  # Ej: "LEC"

        # Buscar cuántos productos existen con cod_interno que empiezan con "LEC-new"
        count = Producto.query.filter(
            Producto.cod_interno.ilike(f"{codigo_proveedor}-new%")
        ).count()
        
        nuevo_cod_interno = f"{codigo_proveedor}-new{count + 1}"

        porcentaje_ganancia = proveedor.porcentaje_ganancia

        precio_ars = data.get('precio_ars') or 0

        producto = Producto(
            cod_interno=nuevo_cod_interno,
            cod_proveedor=codigo_proveedor,
            nombre=data.get('nombre'),
            nombre_corto=data.get('nombre_corto'),
            descripcion=data.get('descripcion'),
            precio_ars=precio_ars,
            precio_usd=data.get('precio_usd'),
            porcentaje_ganancia=porcentaje_ganancia,
            disponibles=data.get('disponibles', 0),
            proveedor_id=data['proveedor_id'],
            categoria_id=data.get('categoria_id'),
            status_id=data.get('status_id'),
            unidad_medida_id=data.get('unidad_medida_id'),
            precio_sugerido=data.get('precio_sugerido'),
            marca_id=data.get('marca_id'),
            ubicacion_local=data.get('ubicacion_local')
        )

        # Calcular precio final con los datos ya cargados
        producto.precio_final = producto.calcular_precio_final()

        db.session.add(producto)
        db.session.commit()

        # Guardar imágenes
        imagenes_base64 = data.get('imagenes_base64', [])
        imagen_portada_index = data.get('imagen_portada_index', 0)

        for i, base64_imagen in enumerate(imagenes_base64[:3]):
            public_id = f"productos/{nuevo_cod_interno}-{i+1}"
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