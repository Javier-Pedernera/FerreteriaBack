import io
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm


def formatear_numero(punto_venta, numero):
    return f"{punto_venta:04d}-{numero:08d}"


def generar_pdf_factura(factura):
    buffer = io.BytesIO()
    print("factura", factura)
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30,
    )

    elements = []
    styles = getSampleStyleSheet()

    numero_formateado = formatear_numero(
        factura.puntoVenta,
        factura.arca_numero_cbte
    )

    # TÍTULO
    elements.append(Paragraph(f"<b>{factura.tipo_descripcion}</b>", styles["Title"]))
    elements.append(Spacer(1, 12))

    # DATOS EMPRESA
    elements.append(Paragraph(f"<b>{factura.empresa_nombre}</b>", styles["Normal"]))
    elements.append(Paragraph(f"CUIT: {factura.empresa_cuit}", styles["Normal"]))
    elements.append(Paragraph(f"Condición IVA: {factura.empresa_iva}", styles["Normal"]))
    elements.append(Spacer(1, 12))

    # DATOS FACTURA
    elements.append(Paragraph(f"N°: {numero_formateado}", styles["Normal"]))
    elements.append(Paragraph(f"Fecha: {factura.fecha}", styles["Normal"]))
    elements.append(Spacer(1, 12))

    # DATOS CLIENTE
    elements.append(Paragraph("<b>Cliente</b>", styles["Heading2"]))
    elements.append(Paragraph(f"{factura.cliente_nombre}", styles["Normal"]))
    elements.append(Paragraph(f"CUIT: {factura.cliente_cuit}", styles["Normal"]))
    elements.append(Paragraph(f"Condición IVA: {factura.cliente_iva}", styles["Normal"]))
    elements.append(Spacer(1, 20))

    # TABLA CONCEPTO
    data = [
        ["Concepto", "Importe"],
        ["Servicios prestados", f"$ {factura.importe_total}"],
    ]

    table = Table(data, colWidths=[120 * mm, 40 * mm])
    table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
        ])
    )

    elements.append(table)
    elements.append(Spacer(1, 20))

    # TOTAL
    elements.append(Paragraph(
        f"<b>TOTAL: $ {factura.importe_total}</b>",
        styles["Heading2"]
    ))
    elements.append(Spacer(1, 20))

    # CAE
    elements.append(Paragraph("<b>Datos de Autorización AFIP</b>", styles["Heading3"]))
    elements.append(Paragraph(f"CAE: {factura.cae}", styles["Normal"]))
    elements.append(Paragraph(f"Vencimiento CAE: {factura.vto_cae}", styles["Normal"]))

    doc.build(elements)

    pdf = buffer.getvalue()
    buffer.close()

    return pdf