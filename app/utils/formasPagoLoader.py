from app.models.forma_pago import FormaPago
from app import db

def initialize_formas_pago():
    default_formas_pago = [
        {'nombre': 'Efectivo', 'descripcion': 'Pago en efectivo al momento de la entrega'},
        {'nombre': 'Tarjeta de Crédito Visa', 'descripcion': 'Pago con tarjeta de crédito en un pago o cuotas Visa'},
        {'nombre': 'Tarjeta de Crédito Master', 'descripcion': 'Pago con tarjeta de crédito en un pago o cuotas Master'},
        {'nombre': 'Tarjeta de Débito Visa', 'descripcion': 'Pago con tarjeta de débito Visa'},
        {'nombre': 'Tarjeta de Débito Master', 'descripcion': 'Pago con tarjeta de débito Master'},
        {'nombre': 'Transferencia Bancaria', 'descripcion': 'Transferencia directa a nuestra cuenta bancaria'},
        {'nombre': 'Mercado Pago', 'descripcion': 'Pago a través de la plataforma Mercado Pago'},
        {'nombre': 'Cuenta Corriente', 'descripcion': 'Cliente con cuenta corriente habilitada'},
        {'nombre': 'QR', 'descripcion': 'Con distintas billeteras virtuales'},
        {'nombre': 'Otro', 'descripcion': 'Otra forma de pago no especificada'}
    ]

    for forma in default_formas_pago:
        if not FormaPago.query.filter_by(nombre=forma['nombre']).first():
            nueva_forma = FormaPago(**forma)
            db.session.add(nueva_forma)

    db.session.commit()