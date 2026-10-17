"""
Backfill: corrige la forma_pago de ventas que ya fueron cobradas por
completo pero quedaron con la forma de pago que tenían al venderse a
cuenta corriente (bug ya corregido en pago_service.py para pagos nuevos -
este script arregla lo histórico).

Por cada venta totalmente paga que todavía tiene forma_pago = "Cuenta
Corriente", busca el último movimiento de pago asociado a esa venta y, si
el Pago real se hizo con otra forma de pago, actualiza la venta para que
coincida. Así "Condición de venta" en la factura (y en cualquier otro
lado que lea venta.forma_pago) refleja cómo se cobró realmente.

Uso (correr desde la raíz del repo, con el venv activado):

    python scripts/backfill_forma_pago_ventas.py
        -> dry-run: solo MUESTRA qué cambiaría, no modifica nada.

    python scripts/backfill_forma_pago_ventas.py --aplicar
        -> aplica los cambios y los guarda.

Recomendado: correrlo primero sin --aplicar, revisar la lista, y recién
ahí correrlo con --aplicar. Probalo primero contra tu base local antes de
correrlo en el droplet.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models.venta import Venta
from app.models.forma_pago import FormaPago
from app.models.pago import Pago
from app.models.movimiento_cliente import MovimientoCliente, TipoMovimientoCliente


def main(aplicar: bool):
    app = create_app()
    with app.app_context():
        cta_cte = FormaPago.query.filter(FormaPago.nombre.ilike('cuenta corriente')).first()
        if not cta_cte:
            print("No se encontró la forma de pago 'Cuenta Corriente'. Nada para hacer.")
            return

        ventas = Venta.query.filter(
            Venta.forma_pago_id == cta_cte.id,
            Venta.pagado >= Venta.total,
        ).order_by(Venta.cliente_id, Venta.id).all()

        print(f"Ventas a cuenta corriente ya totalmente pagas: {len(ventas)}\n")

        candidatas = 0
        sin_pago_encontrado = 0

        for venta in ventas:
            movimiento = (
                MovimientoCliente.query
                .filter_by(venta_id=venta.id, tipo=TipoMovimientoCliente.PAGO)
                .order_by(MovimientoCliente.fecha.desc(), MovimientoCliente.id.desc())
                .first()
            )
            if not movimiento or not movimiento.pago_id:
                sin_pago_encontrado += 1
                continue

            pago = Pago.query.get(movimiento.pago_id)
            if not pago or not pago.forma_pago_id or pago.forma_pago_id == cta_cte.id:
                continue

            nueva_forma = FormaPago.query.get(pago.forma_pago_id)
            nombre_nuevo = nueva_forma.nombre if nueva_forma else f"id {pago.forma_pago_id}"
            candidatas += 1
            print(
                f"Venta #{venta.id} (cliente_id={venta.cliente_id}, "
                f"total=${venta.total}): Cuenta Corriente -> {nombre_nuevo}"
            )
            if aplicar:
                venta.forma_pago_id = pago.forma_pago_id

        print(f"\nVentas pagas sin ningún movimiento de pago registrado (no se tocan): {sin_pago_encontrado}")
        print(f"{'Corregidas' if aplicar else 'Se corregirían'}: {candidatas}")

        if aplicar:
            db.session.commit()
            print("\n✅ Cambios guardados.")
        else:
            print("\nEsto fue un dry-run, no se guardó nada. Volvé a correr con --aplicar para aplicar los cambios.")


if __name__ == '__main__':
    main(aplicar='--aplicar' in sys.argv)
