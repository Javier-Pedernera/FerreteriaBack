from datetime import datetime, timedelta
from decimal import Decimal
from flask import request
from sqlalchemy import case, func
from app import db
from app.models.cliente import Cliente
from app.models.pago import Pago
from app.models.persona_autorizada import PersonaAutorizada
from app.models.venta import Venta
from app.services.status_service import StatusService
from app.models.movimiento_cliente import MovimientoCliente, TipoMovimientoCliente
from config import Config

def safe_decimal(value):
    return Decimal(value) if value is not None else Decimal("0")

def safe_float(value):
    return float(value) if value is not None else 0.0

class ClienteService:

    @staticmethod
    def get_all_clientes():
        return Cliente.query.order_by(Cliente.nombre.asc()).all()

    @staticmethod
    def get_cliente_by_id(cliente_id):
        return Cliente.query.get(cliente_id)

    @staticmethod
    def create_cliente(data):
        cliente = Cliente(
            nombre=data['nombre'],
            razon_social=data.get('razon_social'),
            cuit=data.get('cuit'),
            email=data.get('email'),
            telefono=data.get('telefono'),
            direccion=data.get('direccion'),
            estado_id=data['estado_id'],
            cuenta_corriente_activa=data.get('cuenta_corriente_activa', False)
        )
        db.session.add(cliente)
        db.session.flush()  # Para que cliente tenga ID asignado antes del commit

        # Crear persona autorizada con datos del cliente
        estado_activo = StatusService.get_status_by_code('active')
        persona_autorizada = PersonaAutorizada(
            cliente_id=cliente.id,
            nombre=cliente.nombre,
            apellido='',  # No lo tienes en cliente, podrías extraerlo si está separado
            dni=None,
            email=cliente.email,
            telefono=cliente.telefono,
            estado_id=estado_activo.id if estado_activo else cliente.estado_id,
        )
        db.session.add(persona_autorizada)

        db.session.commit()
        return cliente

    @staticmethod
    def update_cliente(cliente_id, data):
        cliente = Cliente.query.get(cliente_id)
        if not cliente:
            return None

        cliente.nombre = data.get('nombre', cliente.nombre)
        cliente.razon_social = data.get('razon_social', cliente.razon_social)
        cliente.cuit = data.get('cuit', cliente.cuit)
        cliente.email = data.get('email', cliente.email)
        cliente.telefono = data.get('telefono', cliente.telefono)
        cliente.direccion = data.get('direccion', cliente.direccion)
        cliente.estado_id = data.get('estado_id', cliente.estado_id)
        cliente.cuenta_corriente_activa = data.get('cuenta_corriente_activa', cliente.cuenta_corriente_activa)

        # Manejo de personas autorizadas (si se envían)
        personas_data = data.get('personas_autorizadas')
        if personas_data is not None:
            # Borrar las anteriores
            PersonaAutorizada.query.filter_by(cliente_id=cliente.id).delete()

            # Crear nuevas personas con estado 'activo'
            estado_activo = StatusService.get_status_by_code('active')
            for persona in personas_data:
                nueva = PersonaAutorizada(
                    cliente_id=cliente.id,
                    nombre=persona['nombre'],
                    apellido=persona['apellido'],
                    dni=persona.get('dni'),
                    email=persona.get('email'),
                    telefono=persona.get('telefono'),
                    estado_id=estado_activo.id if estado_activo else cliente.estado_id,
                )
                db.session.add(nueva)

        db.session.commit()
        return cliente
    
    @staticmethod
    def get_cliente_con_deuda(
        cliente_id: int,
        desde: str | None = None,
        hasta: str | None = None
    ):
        cliente = Cliente.query.get(cliente_id)
        if not cliente:
            return None

        # -------------------
        # filtros de fechas
        # -------------------
        if desde and hasta:
            desde_dt = datetime.strptime(desde, "%Y-%m-%d")
            hasta_dt = datetime.strptime(hasta, "%Y-%m-%d") + timedelta(days=1)
        elif desde or hasta:
            raise ValueError("Debe enviar 'desde' y 'hasta' juntos")
        else:
            desde_dt = hasta_dt = None

        # -------------------
        # FLAG MIGRACIÓN
        # -------------------
        usar_movimientos = Config.MOVIMIENTOS_CLIENTE_ENABLED

        # =========================================================
        # 🟡 LEGACY (SISTEMA ACTUAL - NO TOCAR)
        # =========================================================

        ventas_q = Venta.query.filter_by(cliente_id=cliente_id)

        estado_deleted = StatusService.get_status_by_code("deleted")
        if estado_deleted:
            ventas_q = ventas_q.filter(Venta.estado_id != estado_deleted.id)

        if desde_dt and hasta_dt:
            ventas_q = ventas_q.filter(
                Venta.fecha_venta >= desde_dt,
                Venta.fecha_venta <= hasta_dt
            )

        ventas = ventas_q.order_by(Venta.id.desc()).all()

        ventas_serializadas = []
        deuda_total_legacy = 0.0

        for v in ventas:
            saldo = float(v.total) - float(v.pagado)
            deuda_total_legacy += saldo

            ventas_serializadas.append({
                "id": v.id,
                "fecha_venta": v.fecha_venta.isoformat(),
                "total": float(v.total),
                "pagado": float(v.pagado),
                "saldo": saldo,
                "observaciones": v.observaciones,
                "estado": v.estado.label if v.estado else None,
                "forma_pago": v.forma_pago.nombre if v.forma_pago else None,
                "retira": v.persona_autorizada.serialize() if v.persona_autorizada else None
            })

        # =========================================================
        # 🔵 MOVIMIENTOS (NUEVO SISTEMA - EN PARALELO)
        # =========================================================

        deuda_total_movimientos = 0.0

        if usar_movimientos:
            mov_q = MovimientoCliente.query.filter_by(cliente_id=cliente_id)

            if desde_dt and hasta_dt:
                mov_q = mov_q.filter(
                    MovimientoCliente.fecha >= desde_dt,
                    MovimientoCliente.fecha <= hasta_dt
                )

            movimientos = mov_q.all()

            for m in movimientos:
                if m.tipo == TipoMovimientoCliente.VENTA:
                    deuda_total_movimientos += float(m.monto)

                elif m.tipo == TipoMovimientoCliente.PAGO:
                    deuda_total_movimientos -= float(m.monto)

                elif m.tipo == TipoMovimientoCliente.CREDITO:
                    deuda_total_movimientos -= float(m.monto)

                elif m.tipo == TipoMovimientoCliente.AJUSTE:
                    deuda_total_movimientos += float(m.monto)

        # -------------------
        # PAGOS (SIN CAMBIOS)
        # -------------------

        pagos_q = Pago.query.filter_by(cliente_id=cliente_id)

        if desde_dt and hasta_dt:
            pagos_q = pagos_q.filter(
                Pago.fecha >= desde_dt,
                Pago.fecha <= hasta_dt
            )

        pagos = pagos_q.order_by(Pago.id.desc()).all()
        pagos_serializados = [p.serialize() for p in pagos]

        # -------------------
        # RESPONSE FINAL
        # -------------------

        return {
            "cliente": cliente.serialize(),
            "ventas": ventas_serializadas,
            "pagos": pagos_serializados,

            # 🟡 SISTEMA ACTUAL (PRODUCCIÓN)
            "deuda_total": deuda_total_legacy,

            # 🔵 NUEVO SISTEMA (PARALELO)
            "deuda_total_movimientos": deuda_total_movimientos,

            # 🧠 CONTROL MIGRACIÓN
            "modo_deuda": "movimientos" if usar_movimientos else "legacy",

            "saldo_favor": float(cliente.saldo_favor or 0)
        }
        
    @staticmethod
    def get_resumen_cuenta_corriente(
        cliente_id: int,
        desde: str | None = None,
        hasta: str | None = None
    ):
        cliente = Cliente.query.get(cliente_id)
        if not cliente:
            return None

        movimientos = []

        # validar fechas si vienen
        if desde and hasta:
            desde_dt = datetime.strptime(desde, "%Y-%m-%d").date()
            hasta_dt = datetime.strptime(hasta, "%Y-%m-%d").date()
        elif desde or hasta:
            raise ValueError("Debe enviar 'desde' y 'hasta' juntos")
        else:
            desde_dt = hasta_dt = None

        # -------------------
        # Ventas
        # -------------------
        ventas_q = cliente.ventas

        estado_deleted = StatusService.get_status_by_code("deleted")
        if estado_deleted:
            ventas_q = [v for v in ventas_q if v.estado_id != estado_deleted.id]

        if desde_dt and hasta_dt:
            ventas_q = [
                v for v in ventas_q
                if desde_dt <= v.fecha_venta.date() <= hasta_dt
            ]

        for v in ventas_q:
            movimientos.append({
                "tipo": "venta",
                "id": v.id,
                "fecha": v.fecha_venta,
                "descripcion": f"Venta #{v.id}",
                "debe": float(v.total),
                "haber": 0.0
            })

        # -------------------
        # Pagos
        # -------------------
        pagos_q = Pago.query.filter_by(cliente_id=cliente_id)

        if desde_dt and hasta_dt:
            pagos_q = pagos_q.filter(
                Pago.fecha >= desde_dt,
                Pago.fecha <= hasta_dt
            )

        pagos = pagos_q.all()

        for p in pagos:
            movimientos.append({
                "tipo": "pago",
                "id": p.id,
                "fecha": p.fecha,
                "descripcion": "Pago registrado",
                "debe": 0.0,
                "haber": float(p.monto)
            })

        # -------------------
        # Orden cronológico
        # -------------------
        movimientos.sort(key=lambda x: x["fecha"])

        # -------------------
        # Saldo acumulado
        # -------------------
        saldo = -float(cliente.saldo_favor or 0)

        for m in movimientos:
            saldo += m["debe"]
            saldo -= m["haber"]
            m["saldo"] = saldo
            m["fecha"] = m["fecha"].isoformat()

        # más nuevo primero
        movimientos.reverse()

        return {
            "cliente": cliente.serialize(),
            "movimientos": movimientos
        }
     
    @staticmethod
    def get_resumen_para_cliente(cliente_id: int):
        cliente = Cliente.query.get(cliente_id)
        if not cliente:
            return None

        hasta = request.args.get("hasta")
        if not hasta:
            raise ValueError("La fecha 'hasta' es obligatoria")

        fecha_hasta = datetime.fromisoformat(hasta)

        estado_on_account = StatusService.get_status_by_code("on_account")
        if not estado_on_account:
            raise Exception("Estado 'on_account' no encontrado")

        estado_deleted = StatusService.get_status_by_code("deleted")

        ventas = (
            Venta.query
            .filter(Venta.cliente_id == cliente_id)
            .filter(Venta.estado_id == estado_on_account.id)
            .filter(Venta.fecha_venta <= fecha_hasta)
        )

        if estado_deleted:
            ventas = ventas.filter(Venta.estado_id != estado_deleted.id)

        ventas = ventas.order_by(Venta.fecha_venta.asc()).all()

        productos_map = {}
        total_consumido = Decimal("0")
        resumen_ventas = []

        for venta in ventas:
            total_consumido += safe_decimal(venta.total)

            resumen_ventas.append({
                "venta_id": venta.id,
                "fecha": venta.fecha_venta.isoformat(),
                "total": safe_float(venta.total),
                "pagado": safe_float(venta.pagado),
                "saldo": safe_float(venta.saldo),
                "detalles": [
                    {
                        "producto_id": d.producto_id,
                        "producto": d.producto.nombre,
                        "cantidad": safe_float(d.cantidad),
                        "precio_unitario": safe_float(d.precio_unitario),
                        "subtotal": safe_float(
                            safe_decimal(d.cantidad) * safe_decimal(d.precio_unitario)
                        ),
                    }
                    for d in venta.detalles
                ],
            })

            for d in venta.detalles:
                key = d.producto_id
                if key not in productos_map:
                    productos_map[key] = {
                        "producto_id": d.producto_id,
                        "producto": d.producto.nombre,
                        "cantidad": Decimal("0"),
                        "subtotal": Decimal("0"),
                    }

                productos_map[key]["cantidad"] += safe_decimal(d.cantidad)
                productos_map[key]["subtotal"] += (
                    safe_decimal(d.cantidad) * safe_decimal(d.precio_unitario)
                )

        productos = [
            {
                "producto_id": p["producto_id"],
                "producto": p["producto"],
                "cantidad": safe_float(p["cantidad"]),
                "subtotal": safe_float(p["subtotal"]),
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
            "hasta": hasta,
            "ventas": resumen_ventas,
            "productos": productos,
            "total_consumido": safe_float(total_consumido),
        }
        
        
    def calcular_deuda_cliente(cliente_id):
        total = db.session.query(
            func.coalesce(
                func.sum(
                    case(
                        (MovimientoCliente.tipo == TipoMovimientoCliente.VENTA, MovimientoCliente.monto),
                        (MovimientoCliente.tipo == TipoMovimientoCliente.PAGO, -MovimientoCliente.monto),
                        (MovimientoCliente.tipo == TipoMovimientoCliente.CREDITO, -MovimientoCliente.monto),
                        (MovimientoCliente.tipo == TipoMovimientoCliente.AJUSTE, MovimientoCliente.monto),  # 🔥 clave
                        else_=0
                    )
                ),
                0
            )
        ).filter(
            MovimientoCliente.cliente_id == cliente_id
        ).scalar()

        return float(total)