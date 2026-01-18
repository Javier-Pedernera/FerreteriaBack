from decimal import Decimal
from datetime import datetime, timezone
from app.models.cliente import Cliente
from app.models.venta import Venta
from app.services.status_service import StatusService


class ResumenCuentaCorrienteService:

    @staticmethod
    def get_resumen_para_cliente(
        cliente_id: int,
        desde: str,
        hasta: str,
        solo_cuenta_corriente: bool = False
    ):
        cliente = Cliente.query.get(cliente_id)
        if not cliente:
            return None

        if not desde or not hasta:
            raise ValueError("Las fechas 'desde' y 'hasta' son obligatorias")

        try:
            fecha_desde = datetime.fromisoformat(desde).replace(tzinfo=timezone.utc)
            fecha_hasta = datetime.fromisoformat(hasta).replace(tzinfo=timezone.utc)
        except ValueError:
            raise ValueError("Formato de fecha inválido. Usar YYYY-MM-DD")

        if fecha_desde > fecha_hasta:
            raise ValueError("'desde' no puede ser mayor que 'hasta'")

        # 🔎 Query base
        query = (
            Venta.query
            .filter(Venta.cliente_id == cliente_id)
            .filter(Venta.fecha_venta >= fecha_desde)
            .filter(Venta.fecha_venta <= fecha_hasta)
        )

        # 🧾 Filtro opcional por cuenta corriente
        if solo_cuenta_corriente:
            estado_on_account = StatusService.get_status_by_code("on_account")
            if not estado_on_account:
                raise Exception("Estado 'on_account' no encontrado")

            query = query.filter(Venta.estado_id == estado_on_account.id)

        ventas = query.order_by(Venta.fecha_venta.asc()).all()

        productos_map = {}
        total_consumido = Decimal("0")
        resumen_ventas = []

        for venta in ventas:
            total_consumido += Decimal(venta.total or 0)

            resumen_ventas.append({
                "venta_id": venta.id,
                "fecha": venta.fecha_venta.isoformat(),
                "estado_id": venta.estado_id,
                "total": float(venta.total),
                "pagado": float(venta.pagado),
                "saldo": float(venta.saldo),
                "detalles": [
                    {
                        "producto_id": d.producto_id,
                        "producto": d.producto.nombre,
                        "cantidad": float(d.cantidad),
                        "precio_unitario": float(d.precio_unitario),
                        "subtotal": float(
                            Decimal(d.cantidad) * Decimal(d.precio_unitario)
                        ),
                    }
                    for d in venta.detalles
                ],
            })

            for d in venta.detalles:
                if d.producto_id not in productos_map:
                    productos_map[d.producto_id] = {
                        "producto_id": d.producto_id,
                        "producto": d.producto.nombre,
                        "cantidad": Decimal("0"),
                        "subtotal": Decimal("0"),
                    }

                productos_map[d.producto_id]["cantidad"] += Decimal(d.cantidad)
                productos_map[d.producto_id]["subtotal"] += (
                    Decimal(d.cantidad) * Decimal(d.precio_unitario)
                )

        productos = [
            {
                "producto_id": p["producto_id"],
                "producto": p["producto"],
                "cantidad": float(p["cantidad"]),
                "subtotal": float(p["subtotal"]),
            }
            for p in productos_map.values()
        ]

        return {
            "cliente": {
                "id": cliente.id,
                "nombre": cliente.nombre,
                "razon_social": cliente.razon_social,
                "cuit": cliente.cuit,
            },
            "desde": desde,
            "hasta": hasta,
            "solo_cuenta_corriente": solo_cuenta_corriente,
            "ventas": resumen_ventas,
            "productos": productos,
            "total_consumido": float(total_consumido),
        }