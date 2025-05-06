from sqlalchemy import event
from app.models.producto import Producto

@event.listens_for(Producto, 'before_insert')
@event.listens_for(Producto, 'before_update')
def calcular_precio_final(mapper, connection, target):
    try:
        porcentaje = target.porcentaje_ganancia or target.proveedor.porcentaje_ganancia
        target.precio_final = round(float(target.precio_ars) * (1 + porcentaje / 100), 2)
    except Exception:
        target.precio_final = None