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
    ruta_excel = f'./app/static/uploads/excels/{nombre_archivo}'
    extension = nombre_archivo.split('.')[-1].lower()

    col_codigo = plantilla.nombre_columna_codigo
    dtype = {col_codigo: str}

    try:
        engine = 'xlrd' if extension == 'xls' else 'openpyxl'
        df = pd.read_excel(
            ruta_excel,
            engine=engine,
            skiprows=plantilla.fila_inicio - 1,
            dtype=dtype
        )
        df.columns = df.columns.str.strip()
    except Exception as e:
        return {"error": f"Error al cargar el archivo Excel: {str(e)}"}

    proveedor = Proveedor.query.get(plantilla.proveedor_id)
    if not proveedor:
        return {"error": "Proveedor no encontrado."}

    codigo_proveedor = proveedor.codigo_proveedor
    productos_importados = 0
    errores = []

    for index, row in df.iterrows():
        try:
            if col_codigo not in df.columns:
                return {"error": f"La columna '{col_codigo}' no existe en el archivo Excel."}

            codigo_producto = row[col_codigo]
            if pd.isna(codigo_producto) or not str(codigo_producto).strip():
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
                if plantilla.delimitador_decimal == ',':
                    precio_ars = precio_ars.replace(',', '.')

            try:
                precio_ars = round(float(precio_ars), 2)
            except ValueError:
                continue

            if not proveedor.precio_con_iva:
                precio_ars = round(precio_ars * 1.21, 2)

            precio_usd = round(precio_ars / cotizacion_dolar, 2)

            nombre = None
            if plantilla.nombre_columna_nombre in df.columns:
                val = row.get(plantilla.nombre_columna_nombre)
                if val and str(val).strip():
                    nombre = val

            descripcion = None
            if plantilla.nombre_columna_descripcion in df.columns:
                val = row.get(plantilla.nombre_columna_descripcion)
                if val and str(val).strip():
                    descripcion = val

            nombre_corto = None
            actualizar_nombre_corto = False
            if plantilla.nombre_columna_nombre_corto in df.columns:
                val = row.get(plantilla.nombre_columna_nombre_corto)
                if val and str(val).strip():
                    nombre_corto = val
                    actualizar_nombre_corto = True

            ubicacion_local = None
            actualizar_ubicacion = False
            if plantilla.nombre_columna_ubicacion in df.columns:
                val = row.get(plantilla.nombre_columna_ubicacion)
                if val and str(val).strip():
                    ubicacion_local = val
                    actualizar_ubicacion = True

            unidad_medida_id = None
            actualizar_unidad = False
            if plantilla.nombre_columna_unidad_medida in df.columns:
                val = row.get(plantilla.nombre_columna_unidad_medida)
                if val and str(val).strip():
                    unidad = UnidadMedida.query.filter_by(
                        codigo=str(val).strip()
                    ).first()
                    if unidad:
                        unidad_medida_id = unidad.id
                        actualizar_unidad = True

            presentacion_cantidad = None
            actualizar_presentacion = False
            if plantilla.nombre_columna_presentacion in df.columns:
                val = row.get(plantilla.nombre_columna_presentacion)
                if val and str(val).strip().lower() != "nan":
                    try:
                        presentacion_cantidad = float(str(val).replace(",", "."))
                        actualizar_presentacion = True
                    except ValueError:
                        pass

            es_fraccionable = None
            actualizar_es_fraccionable = False
            if plantilla.nombre_columna_es_fraccionable in df.columns:
                val = row.get(plantilla.nombre_columna_es_fraccionable)
                if val and str(val).strip().lower() != "nan":
                    es_fraccionable = str(val).strip().lower() in ["1", "si", "sí", "true"]
                    actualizar_es_fraccionable = True

            porcentaje_ganancia = None
            actualizar_pg = False
            if plantilla.nombre_columna_porcentaje_ganancia in df.columns:
                val = row.get(plantilla.nombre_columna_porcentaje_ganancia)
                if val and str(val).strip().lower() != "nan":
                    try:
                        porcentaje_ganancia = float(str(val).replace(",", "."))
                        actualizar_pg = True
                    except ValueError:
                        pass

            porcentaje_ganancia_personalizado = None
            actualizar_pg_personalizado = False
            if plantilla.nombre_columna_pg_personalizado in df.columns:
                val = row.get(plantilla.nombre_columna_pg_personalizado)
                if val and str(val).strip().lower() != "nan":
                    porcentaje_ganancia_personalizado = str(val).strip().lower() in ["1", "si", "sí", "true"]
                    actualizar_pg_personalizado = True

            producto_existente = Producto.query.filter_by(
                cod_interno=f"{codigo_proveedor}-{codigo_str}"
            ).first()

            if producto_existente:
                producto_existente.precio_ars = precio_ars
                producto_existente.precio_usd = precio_usd

                if nombre:
                    producto_existente.nombre = nombre
                if descripcion:
                    producto_existente.descripcion = descripcion
                if actualizar_nombre_corto:
                    producto_existente.nombre_corto = nombre_corto
                if actualizar_ubicacion:
                    producto_existente.ubicacion_local = ubicacion_local
                if actualizar_unidad:
                    producto_existente.unidad_medida_id = unidad_medida_id
                if actualizar_presentacion:
                    producto_existente.presentacion_cantidad = presentacion_cantidad
                if actualizar_es_fraccionable:
                    producto_existente.es_fraccionable = es_fraccionable
                if actualizar_pg:
                    producto_existente.porcentaje_ganancia = porcentaje_ganancia
                if actualizar_pg_personalizado:
                    producto_existente.porcentaje_ganancia_personalizado = porcentaje_ganancia_personalizado

                if status_out_of_stock:
                    producto_existente.status_id = status_out_of_stock.id

                db.session.flush()
                producto_existente.precio_final = producto_existente.calcular_precio_final()

            else:
                producto = Producto(
                    cod_interno=f"{codigo_proveedor}-{codigo_str}",
                    cod_proveedor=codigo_proveedor,
                    nombre=nombre,
                    descripcion=descripcion,
                    precio_ars=precio_ars,
                    precio_usd=precio_usd,
                    proveedor_id=proveedor.id,
                    status_id=status_out_of_stock.id if status_out_of_stock else None,
                    porcentaje_ganancia=porcentaje_ganancia if actualizar_pg else proveedor.porcentaje_ganancia,
                    porcentaje_ganancia_personalizado=porcentaje_ganancia_personalizado if actualizar_pg_personalizado else False
                )
                db.session.add(producto)
                db.session.flush()
                producto.precio_final = producto.calcular_precio_final()

            productos_importados += 1

        except Exception as e:
            errores.append(f"Fila {index + plantilla.fila_inicio}: {str(e)}")

    try:
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        return {"error": str(e)}

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