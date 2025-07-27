from sqlalchemy import asc
from app import db
from app.models.planilla_importacion import PlantillaImportacion
from datetime import datetime, timezone
import pandas as pd
from app.models.producto import Producto
from app.models.proveedor import Proveedor
from app.models.categoria import Categoria
from app.models.marca import Marca
from app.models.status import Status
from sqlalchemy.exc import SQLAlchemyError

from app.models.unidad_medida import UnidadMedida

def create_import_template(data):
    nueva_plantilla = PlantillaImportacion(
        proveedor_id=data['proveedor_id'],
        nombre_archivo_excel=data['nombre_archivo_excel'],
        nombre_columna_codigo=data['nombre_columna_codigo'],
        nombre_columna_precio=data['nombre_columna_precio'],
        nombre_columna_nombre=data.get('nombre_columna_nombre'),
        nombre_columna_precio_sugerido=data.get('nombre_columna_precio_sugerido'),
        nombre_columna_descripcion=data.get('nombre_columna_descripcion'),
        nombre_columna_marca=data.get('nombre_columna_marca'),
        nombre_columna_categoria=data.get('nombre_columna_categoria'),
        nombre_columna_nombre_corto=data.get('nombre_columna_nombre_corto'),
        nombre_columna_ubicacion=data.get('nombre_columna_ubicacion'),
        nombre_columna_unidad_medida=data.get('nombre_columna_unidad_medida'),
        nombre_columna_presentacion=data.get('nombre_columna_presentacion'),
        nombre_columna_es_fraccionable=data.get('nombre_columna_es_fraccionable'),
        nombre_columna_porcentaje_ganancia=data.get('nombre_columna_porcentaje_ganancia'),
        nombre_columna_pg_personalizado=data.get('nombre_columna_pg_personalizado'),
        fila_inicio=data.get('fila_inicio', 2),
        delimitador_decimal=data.get('delimitador_decimal', '.'),
        usa_simbolo_pesos=data.get('usa_simbolo_pesos', True),
        usa_miles_con_punto=data.get('usa_miles_con_punto', True),
        cod_solo_numero=data.get('cod_solo_numero', False),
        fecha_creacion=datetime.now(timezone.utc),
        fecha_actualizacion=datetime.now(timezone.utc),
    )
    db.session.add(nueva_plantilla)
    db.session.commit()
    return nueva_plantilla

def import_products_from_excel(plantilla_id, cotizacion_dolar, fecha_lista):
    # Validar cotización
    status_out_of_stock = Status.query.filter_by(code='out of stock').first()
    if not cotizacion_dolar or cotizacion_dolar <= 0:
        return {"error": "La cotización del dólar debe ser un número positivo."}
    if not fecha_lista:
        return {"error": "Debe proporcionar la fecha de la lista."}
    try:
        fecha_lista_dt = datetime.fromisoformat(fecha_lista)
    except ValueError:
        return {"error": "Formato de fecha inválido. Use YYYY-MM-DD o ISO completo."}

    plantilla = PlantillaImportacion.query.get(plantilla_id)
    if not plantilla:
        return {"error": "No se encontró la plantilla con ese ID."}
    plantilla.fecha_ultima_lista = fecha_lista_dt
    nombre_archivo = plantilla.nombre_archivo_excel
    print("nombre del excel......", nombre_archivo)
    ruta_excel = f'./app/static/uploads/excels/{nombre_archivo}'

    extension = nombre_archivo.split('.')[-1].lower()

    col_codigo = plantilla.nombre_columna_codigo
    dtype = {col_codigo: str}

    try:
        if extension == 'xls':
            df = pd.read_excel(ruta_excel, engine='xlrd', skiprows=plantilla.fila_inicio - 1, dtype=dtype)
        else:
            df = pd.read_excel(ruta_excel, engine='openpyxl', skiprows=plantilla.fila_inicio - 1, dtype=dtype)
        df.columns = df.columns.str.strip()
    except Exception as e:
        return {"error": f"Error al cargar el archivo Excel: {str(e)}"}

    print("Columnas encontradas en el Excel:", df.columns.tolist())

    proveedor = Proveedor.query.get(plantilla.proveedor_id)
    if not proveedor:
        return {"error": "Proveedor no encontrado."}

    nombre_proveedor = proveedor.nombre.strip().lower().replace(" ", "")
    nombre_archivo_simple = nombre_archivo.strip().lower().replace(" ", "")

    if nombre_proveedor not in nombre_archivo_simple:
        return {
            "error": f"El nombre del archivo '{nombre_archivo}' no parece corresponder al proveedor '{proveedor.nombre}'. Verifique que esté usando el archivo correcto."
        }

    codigo_proveedor = proveedor.codigo_proveedor
    productos_importados = 0
    errores = []

    for index, row in df.iterrows():
        try:
            col_codigo = plantilla.nombre_columna_codigo
            if col_codigo not in df.columns:
                return {"error": f"La columna '{col_codigo}' no existe en el archivo Excel."}

            codigo_producto = row[col_codigo]
            if pd.isna(codigo_producto) or str(codigo_producto).strip() == "":
                continue
            codigo_str = str(codigo_producto).strip()
            if plantilla.cod_solo_numero and not codigo_str.isdigit():
                continue
            if codigo_str.isdigit():
                codigo_str = str(int(codigo_str))

            precio_ars = row[plantilla.nombre_columna_precio]
            if pd.isna(precio_ars):
                continue

            if isinstance(precio_ars, str):
                if plantilla.usa_simbolo_pesos:
                    precio_ars = precio_ars.replace('$', '')
                if plantilla.usa_miles_con_punto:
                    precio_ars = precio_ars.replace('.', '')
                precio_ars = precio_ars.replace(',', '.') if plantilla.delimitador_decimal == ',' else precio_ars

            try:
                precio_ars = round(float(precio_ars), 2)
            except ValueError:
                continue

            # 🔹 APLICAR IVA SI ES NECESARIO
            if not proveedor.precio_con_iva:
                precio_ars = round(precio_ars * 1.21, 2)

            precio_usd = round(precio_ars / cotizacion_dolar, 2)
            
            nombre = None
            if plantilla.nombre_columna_nombre and plantilla.nombre_columna_nombre in df.columns:
                nombre = row.get(plantilla.nombre_columna_nombre)
                if pd.isna(nombre) or str(nombre).strip() == "":
                    nombre = None

            if not nombre:
                nombre = row.get(plantilla.nombre_columna_descripcion, "")
                if pd.isna(nombre) or str(nombre).strip() == "":
                    nombre = None

            precio_sugerido = row.get(plantilla.nombre_columna_precio_sugerido) if plantilla.nombre_columna_precio_sugerido else None

            marca = None
            if plantilla.nombre_columna_marca:
                marca_nombre = row.get(plantilla.nombre_columna_marca)
                if pd.isna(marca_nombre) or str(marca_nombre).strip() == "":
                    marca = None
                else:
                    marca = Marca.query.filter_by(nombre=marca_nombre).first()
                    if not marca:
                        marca = Marca(nombre=marca_nombre)
                        db.session.add(marca)
                        db.session.commit()

            categoria = None
            if plantilla.nombre_columna_categoria:
                categoria_nombre = row.get(plantilla.nombre_columna_categoria)

                # Ignorar si viene NaN, None o vacío
                if categoria_nombre and str(categoria_nombre).strip().lower() != 'nan':
                    categoria = Categoria.query.filter_by(nombre=str(categoria_nombre).strip()).first()

            descripcion = None
            if plantilla.nombre_columna_descripcion and plantilla.nombre_columna_descripcion in df.columns:
                descripcion_valor = row.get(plantilla.nombre_columna_descripcion)
                if not pd.isna(descripcion_valor) and str(descripcion_valor).strip() != "":
                    descripcion = str(descripcion_valor).strip()

            # Campos nuevos
            nombre_corto = None
            if plantilla.nombre_columna_nombre_corto and plantilla.nombre_columna_nombre_corto in df.columns:
                nombre_corto = row.get(plantilla.nombre_columna_nombre_corto)
                if pd.isna(nombre_corto) or str(nombre_corto).strip() == "":
                    nombre_corto = None

            ubicacion_local = None
            if plantilla.nombre_columna_ubicacion and plantilla.nombre_columna_ubicacion in df.columns:
                ubicacion_local = row.get(plantilla.nombre_columna_ubicacion)
                if pd.isna(ubicacion_local) or str(ubicacion_local).strip() == "":
                    ubicacion_local = None

            unidad_medida_id = None
            if plantilla.nombre_columna_unidad_medida and plantilla.nombre_columna_unidad_medida in df.columns:
                unidad_nombre = row.get(plantilla.nombre_columna_unidad_medida)
                if not pd.isna(unidad_nombre) and str(unidad_nombre).strip():
                    unidad = UnidadMedida.query.filter_by(codigo=str(unidad_nombre).strip()).first()
                    # print(unidad)
                    if unidad:
                        unidad_medida_id = unidad.id

            presentacion_cantidad = None
            if plantilla.nombre_columna_presentacion and plantilla.nombre_columna_presentacion in df.columns:
                valor = row.get(plantilla.nombre_columna_presentacion)
                if valor is not None and str(valor).strip().lower() != "nan":
                    try:
                        presentacion_cantidad = float(str(valor).replace(",", "."))
                    except ValueError:
                        presentacion_cantidad = None

            es_fraccionable = False
            if plantilla.nombre_columna_es_fraccionable and plantilla.nombre_columna_es_fraccionable in df.columns:
                val = row.get(plantilla.nombre_columna_es_fraccionable)
                if val is not None and str(val).strip().lower() != "nan":
                    es_fraccionable = str(val).strip().lower() in ["1", "sí", "si", "true"]

            porcentaje_ganancia = proveedor.porcentaje_ganancia
            if plantilla.nombre_columna_porcentaje_ganancia and plantilla.nombre_columna_porcentaje_ganancia in df.columns:
                raw = row.get(plantilla.nombre_columna_porcentaje_ganancia)
                if raw is not None and str(raw).strip().lower() != "nan":
                    try:
                        porcentaje_ganancia = float(str(raw).replace(",", "."))
                    except ValueError:
                        porcentaje_ganancia = proveedor.porcentaje_ganancia

            porcentaje_ganancia_personalizado = False
            if plantilla.nombre_columna_pg_personalizado and plantilla.nombre_columna_pg_personalizado in df.columns:
                val = row.get(plantilla.nombre_columna_pg_personalizado)
                if val is not None and str(val).strip().lower() != "nan":
                    porcentaje_ganancia_personalizado = str(val).strip().lower() in ["1", "sí", "si", "true"]
            producto_existente = Producto.query.filter_by(cod_interno=f"{codigo_proveedor}-{codigo_str}").first()

            if producto_existente:
                producto_existente.precio_ars = precio_ars
                producto_existente.precio_usd = precio_usd
                producto_existente.precio_sugerido = precio_sugerido
                producto_existente.marca_id = marca.id if marca else None
                producto_existente.categoria_id = categoria.id if categoria else None
                producto_existente.nombre = nombre
                producto_existente.descripcion = descripcion
                producto_existente.nombre_corto = nombre_corto
                producto_existente.ubicacion_local = ubicacion_local
                producto_existente.unidad_medida_id = unidad_medida_id
                producto_existente.presentacion_cantidad = presentacion_cantidad
                producto_existente.es_fraccionable = es_fraccionable
                producto_existente.porcentaje_ganancia = porcentaje_ganancia
                producto_existente.porcentaje_ganancia_personalizado = porcentaje_ganancia_personalizado
                db.session.flush()
                db.session.refresh(producto_existente)

                producto_existente.precio_final = producto_existente.calcular_precio_final()
            else:
                producto = Producto(
                    cod_interno=f"{codigo_proveedor}-{codigo_str}",
                    cod_proveedor=codigo_proveedor,
                    nombre=nombre,
                    nombre_corto=nombre_corto,
                    precio_ars=precio_ars,
                    precio_usd=precio_usd,
                    precio_sugerido=precio_sugerido,
                    proveedor_id=proveedor.id,
                    categoria_id=categoria.id if categoria else None,
                    status_id=status_out_of_stock.id if status_out_of_stock else None,
                    marca_id=marca.id if marca else None,
                    descripcion=descripcion,
                    disponibles=0,
                    ubicacion_local=ubicacion_local,
                    unidad_medida_id=unidad_medida_id,
                    presentacion_cantidad=presentacion_cantidad,
                    es_fraccionable=es_fraccionable,
                    porcentaje_ganancia=porcentaje_ganancia,
                    porcentaje_ganancia_personalizado=porcentaje_ganancia_personalizado,
                )
                # producto.precio_final = producto.calcular_precio_final()
                db.session.add(producto)
                db.session.flush()
                producto.precio_final = producto.calcular_precio_final()
            productos_importados += 1
        except Exception as e:
            print(f"Error en fila {index + plantilla.fila_inicio}: {str(e)}")
            print("Contenido de la fila:", row.to_dict())
            errores.append(f"Error en la fila {index + plantilla.fila_inicio}: {str(e)}")
            continue

    try:
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        return {"error": f"Error al guardar en base de datos: {str(e)}"}

    return {
        "processed_count": productos_importados,
        "errors": errores
    }


def get_all_import_templates():
    return PlantillaImportacion.query.order_by(asc(PlantillaImportacion.nombre_archivo_excel)).all()

def get_import_template_by_id(template_id):
    plantilla = PlantillaImportacion.query.get_or_404(template_id)
    return plantilla

def update_import_template(template_id, data):
    plantilla = PlantillaImportacion.query.get_or_404(template_id)
    for key, value in data.items():
        setattr(plantilla, key, value)
    db.session.commit()
    return plantilla

def delete_import_template(template_id):
    plantilla = PlantillaImportacion.query.get_or_404(template_id)
    db.session.delete(plantilla)
    db.session.commit()