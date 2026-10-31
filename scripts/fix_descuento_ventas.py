"""
Backfill: corrige el campo `descuento` de ventas cobradas antes de que se
arreglara el bug en CobrarVentaModal.tsx. Ese bug mandaba el MONTO del
descuento (en pesos) en vez del PORCENTAJE, así que quedaron ventas con
`descuento` guardado como, por ejemplo, 32430.8 (que en realidad eran
$32.430,80 de descuento sobre un total de $405.385, o sea 8%).

Como ningún porcentaje real puede ser mayor a 100, cualquier venta con
`descuento > 100` quedó afectada por este bug. Para esas filas, el
porcentaje real se recupera con `descuento_guardado / total * 100` (porque
el monto guardado es justo `total * pct_real / 100`).

Cuando la venta no quedó a cuenta corriente (pagado > 0), se verifica además
que `total - descuento_guardado` coincida con `pagado` centavo a centavo,
como confirmación cruzada de que es este bug y no otro dato raro. Si no
coincide, la fila se deja sin tocar y se marca para revisión manual.

Uso (correr desde la raíz del repo, con el venv activado):

    python scripts/fix_descuento_ventas.py
        -> dry-run: solo MUESTRA qué cambiaría, no modifica nada.

    python scripts/fix_descuento_ventas.py --aplicar
        -> aplica los cambios y los guarda.

Recomendado: correrlo primero sin --aplicar, revisar la lista, y recién
ahí correrlo con --aplicar. Probalo primero contra tu base local antes de
correrlo en el droplet.
"""
import sys
import os
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models.venta import Venta


def main(aplicar: bool):
    app = create_app()
    with app.app_context():
        ventas = Venta.query.filter(Venta.descuento > 100).order_by(Venta.id).all()

        print(f"Ventas con descuento > 100% (candidatas): {len(ventas)}\n")

        corregidas = 0
        a_revisar_manual = 0

        for venta in ventas:
            total = Decimal(venta.total or 0)
            descuento_actual = Decimal(venta.descuento or 0)
            pagado = Decimal(venta.pagado or 0)

            if total <= 0:
                print(f"Venta #{venta.id}: total es 0, no se puede calcular el % real. Revisar a mano.")
                a_revisar_manual += 1
                continue

            pct_real = (descuento_actual / total * 100).quantize(Decimal('0.01'))

            if pct_real > 100:
                print(
                    f"Venta #{venta.id}: descuento={descuento_actual}, total={total} -> "
                    f"el % derivado ({pct_real}%) tampoco es válido. Revisar a mano."
                )
                a_revisar_manual += 1
                continue

            if pagado > 0:
                reconciliado = abs((total - descuento_actual) - pagado) < Decimal('0.01')
            else:
                # Venta a cuenta corriente (pagado = 0): no hay con qué cruzar el
                # dato, pero el patrón del bug (descuento > 100) ya es suficiente
                # indicio.
                reconciliado = None

            if reconciliado is False:
                print(
                    f"Venta #{venta.id}: descuento={descuento_actual}, total={total}, "
                    f"pagado={pagado} -> NO coincide con el patrón esperado. Revisar a mano."
                )
                a_revisar_manual += 1
                continue

            etiqueta = "(cuenta corriente, sin verificación cruzada)" if reconciliado is None else "(verificado con pagado)"
            print(
                f"Venta #{venta.id}: descuento {descuento_actual} -> {pct_real}% "
                f"{etiqueta}"
            )
            corregidas += 1
            if aplicar:
                venta.descuento = pct_real

        print(f"\n{'Corregidas' if aplicar else 'Se corregirían'}: {corregidas}")
        print(f"A revisar a mano (no se tocaron): {a_revisar_manual}")

        if aplicar:
            db.session.commit()
            print("\n✅ Cambios guardados.")
        else:
            print("\nEsto fue un dry-run, no se guardó nada. Volvé a correr con --aplicar para aplicar los cambios.")


if __name__ == '__main__':
    main(aplicar='--aplicar' in sys.argv)
