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

def create_import_template(data):
    nueva_plantilla = PlantillaImportacion(
        proveedor_id=data['proveedor_id'],
        nombre_archivo_excel=data['nombre_archivo_excel'],
        nombre_columna_codigo=data['nombre_columna_codigo'],
        nombre_columna_precio=data['nombre_columna_precio'],
        nombre_columna_nombre=data['nombre_columna_nombre'],
        nombre_columna_precio_sugerido=data.get('nombre_columna_precio_sugerido'),
        nombre_columna_descripcion=data.get('nombre_columna_descripcion'),
        nombre_columna_marca=data.get('nombre_columna_marca'),
        nombre_columna_categoria=data.get('nombre_columna_categoria'),
        fila_inicio=data.get('fila_inicio', 2),
        delimitador_decimal=data.get('delimitador_decimal', '.'),
        usa_simbolo_pesos=data.get('usa_simbolo_pesos', True),
        usa_miles_con_punto=data.get('usa_miles_con_punto', True),
        fecha_creacion=datetime.now(timezone.utc),
        fecha_actualizacion=datetime.now(timezone.utc),
        cod_solo_numero=data.get('cod_solo_numero', False),
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
            # verifica si el codigo no esta vacia la celda
            if pd.isna(codigo_producto) or str(codigo_producto).strip() == "":
                continue
            codigo_str = str(codigo_producto).strip()
            # verifica si son solo numeros si tiene solo numero en true
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

            # ✅ Calcular precio en dólares
            precio_usd = round(precio_ars / cotizacion_dolar, 2)

            nombre = None
            if plantilla.nombre_columna_nombre and plantilla.nombre_columna_nombre in df.columns:
                nombre = row.get(plantilla.nombre_columna_nombre)
                if pd.isna(nombre) or str(nombre).strip() == "":
                    nombre = None

            # Si no hay nombre, usar descripción si existe
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
                if categoria_nombre:
                    categoria = Categoria.query.filter_by(nombre=categoria_nombre).first()

            # status = Status.query.first()

            producto_existente = Producto.query.filter_by(cod_interno=f"{codigo_proveedor}-{codigo_str}").first()
            
            if producto_existente:
                producto_existente.precio_ars = precio_ars
                producto_existente.precio_usd = precio_usd  # ✅ nuevo campo
                producto_existente.precio_sugerido = precio_sugerido
                producto_existente.marca_id = marca.id if marca else None
                producto_existente.categoria_id = categoria.id if categoria else None
                producto_existente.nombre = nombre
                producto_existente.precio_final = producto_existente.calcular_precio_final()
            else:
                producto = Producto(
                    cod_interno=f"{codigo_proveedor}-{codigo_str}",
                    cod_proveedor=codigo_proveedor,
                    nombre=nombre,
                    precio_ars=precio_ars,
                    precio_usd=precio_usd, 
                    precio_sugerido=precio_sugerido,
                    proveedor_id=proveedor.id,
                    categoria_id=categoria.id if categoria else None,
                    status_id=status_out_of_stock.id if status_out_of_stock else None,
                    marca_id=marca.id if marca else None,
                    cantidad=0,
                    porcentaje_ganancia=proveedor.porcentaje_ganancia,
                )
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

