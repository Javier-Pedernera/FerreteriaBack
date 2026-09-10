import base64
import io
import json

import requests
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing

from app.services.empresa_fiscal_service import EmpresaFiscalService

# Paleta: acento oscuro neutro (el logo es blanco/negro, no tiene color propio
# del que tomar un acento).
COLOR_ACENTO = colors.HexColor("#20242c")
COLOR_ACENTO_SUAVE = colors.HexColor("#eceef1")
COLOR_TEXTO_SUAVE = colors.HexColor("#5a5f68")


def formatear_numero(punto_venta, numero):
    if not punto_venta or not numero:
        return "(sin emitir)"
    return f"{punto_venta:04d}-{numero:08d}"


def _datos_receptor(cliente):
    """Mismo criterio que arca_service.wsfe_autorizar para DocTipo/DocNro."""
    if not cliente or not cliente.tipo_documento:
        return 99, 0

    doc_tipo = cliente.tipo_documento.codigo_afip
    if doc_tipo == 99:
        return doc_tipo, 0
    if not cliente.cuit:
        return doc_tipo, 0
    return doc_tipo, int(cliente.cuit)


def construir_url_qr_afip(factura, empresa):
    """
    Arma la URL del QR exigido por AFIP (RG 4892) para comprobantes
    electrónicos: https://www.afip.gob.ar/fe/qr/?p=<json en base64>
    """
    cliente = factura.cliente
    doc_tipo, doc_nro = _datos_receptor(cliente)

    fecha = factura.fecha_emision or (
        factura.fecha_creacion.date() if factura.fecha_creacion else None
    )

    tipo_cmp = factura.arca_tipo_cbte or (
        factura.tipo_comprobante.codigo_afip if factura.tipo_comprobante else None
    )
    pto_vta = factura.punto_venta_emitido or (
        factura.punto_venta.numero if factura.punto_venta else None
    )

    payload = {
        "ver": 1,
        "fecha": fecha.isoformat() if fecha else None,
        "cuit": int(empresa.cuit) if empresa and empresa.cuit else None,
        "ptoVta": pto_vta,
        "tipoCmp": tipo_cmp,
        "nroCmp": factura.arca_numero_cbte,
        "importe": float(factura.total),
        "moneda": "PES",
        "ctz": 1,
        "tipoDocRec": doc_tipo,
        "nroDocRec": doc_nro,
        "tipoCodAut": "E",
        "codAut": int(factura.arca_cae) if factura.arca_cae else None,
    }

    codificado = base64.b64encode(json.dumps(payload).encode()).decode()
    return f"https://www.afip.gob.ar/fe/qr/?p={codificado}"


def _qr_drawing(url, tamano=32 * mm):
    widget = QrCodeWidget(url)
    x0, y0, x1, y1 = widget.getBounds()
    ancho, alto = x1 - x0, y1 - y0
    drawing = Drawing(tamano, tamano, transform=[tamano / ancho, 0, 0, tamano / alto, 0, 0])
    drawing.add(widget)
    return drawing


def _logo_flowable(logo_url, alto=20 * mm):
    """Descarga el logo y lo devuelve como Image de reportlab. None si falla."""
    if not logo_url:
        return None
    try:
        resp = requests.get(logo_url, timeout=8)
        resp.raise_for_status()
        img = Image(io.BytesIO(resp.content))
        proporcion = img.imageWidth / img.imageHeight
        img.drawHeight = alto
        img.drawWidth = alto * proporcion
        return img
    except Exception:
        return None


def _doc_receptor_texto(cliente):
    if not cliente or not cliente.tipo_documento:
        return "-"
    if cliente.tipo_documento.codigo_afip == 99:
        return "Consumidor Final"
    return f"{cliente.tipo_documento.descripcion}: {cliente.cuit or '-'}"


def generar_pdf_factura(factura):
    """
    Genera el PDF de una Factura real (modelo app.models.factura.Factura).
    """
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=25 * mm,
        leftMargin=25 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
    )

    elements = []
    base = getSampleStyleSheet()

    normal = ParagraphStyle("normal", parent=base["Normal"], fontSize=9, leading=13)
    normal_suave = ParagraphStyle("normal_suave", parent=normal, textColor=COLOR_TEXTO_SUAVE)
    etiqueta = ParagraphStyle("etiqueta", parent=normal, fontSize=8, textColor=COLOR_TEXTO_SUAVE)
    razon_social_style = ParagraphStyle("razon_social", parent=base["Heading2"], fontSize=14, leading=16)
    seccion = ParagraphStyle("seccion", parent=base["Heading4"], fontSize=10, textColor=COLOR_ACENTO, spaceAfter=4)
    centrado = ParagraphStyle("centrado", parent=normal, alignment=TA_CENTER)
    letra_grande = ParagraphStyle("letra_grande", parent=base["Title"], fontSize=34, alignment=TA_CENTER, leading=36)
    derecha = ParagraphStyle("derecha", parent=normal, alignment=TA_RIGHT)
    total_style = ParagraphStyle("total_style", parent=base["Heading2"], alignment=TA_RIGHT, fontSize=16)

    try:
        empresa = EmpresaFiscalService.get_empresa_activa()
    except ValueError:
        empresa = None

    cliente = factura.cliente
    tipo = factura.tipo_comprobante

    punto_venta_numero = factura.punto_venta_emitido or (
        factura.punto_venta.numero if factura.punto_venta else None
    )
    numero_formateado = formatear_numero(punto_venta_numero, factura.arca_numero_cbte)
    fecha = factura.fecha_emision or (
        factura.fecha_creacion.date() if factura.fecha_creacion else None
    )
    codigo_afip = tipo.codigo_afip if tipo else factura.arca_tipo_cbte

    # =========================================================
    # ENCABEZADO: logo + datos emisor  |  recuadro letra/n° comprobante
    # =========================================================
    logo_img = _logo_flowable(empresa.logo_url if empresa else None)

    datos_emisor = [
        Paragraph(empresa.razon_social if empresa else "-", razon_social_style),
        Paragraph(f"CUIT: {empresa.cuit if empresa else '-'}", normal),
        Paragraph(
            f"Condición frente al IVA: {empresa.condicion_iva.descripcion if empresa and empresa.condicion_iva else '-'}",
            normal
        ),
    ]
    if factura.punto_venta and factura.punto_venta.direccion:
        datos_emisor.append(Paragraph(f"Domicilio comercial: {factura.punto_venta.direccion}", normal))

    celda_emisor = []
    if logo_img:
        celda_emisor.append(logo_img)
        celda_emisor.append(Spacer(1, 6))
    celda_emisor.extend(datos_emisor)

    letra = tipo.letra if tipo else "-"
    recuadro_tipo = Table(
        [
            [Paragraph(letra, letra_grande)],
            [Paragraph(f"COD. {codigo_afip:03d}" if codigo_afip else "-", centrado)],
        ],
        colWidths=[28 * mm],
    )
    recuadro_tipo.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1.2, COLOR_ACENTO),
        ("LINEBELOW", (0, 0), (-1, 0), 1, COLOR_ACENTO),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, 0), 4),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 4),
    ]))

    datos_comprobante = [
        recuadro_tipo,
        Spacer(1, 6),
        Paragraph(f"<b>{tipo.descripcion if tipo else 'Comprobante'}</b>", centrado),
        Paragraph(f"N° {numero_formateado}", centrado),
        Paragraph(f"Fecha de emisión: {fecha.isoformat() if fecha else '-'}", centrado),
    ]

    header_table = Table(
        [[celda_emisor, datos_comprobante]],
        colWidths=[105 * mm, 55 * mm],
    )
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (1, 0), (1, 0), "CENTER"),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 10))
    elements.append(HRFlowable(width="100%", thickness=1, color=COLOR_ACENTO))
    elements.append(Spacer(1, 10))

    # =========================================================
    # DATOS DEL CLIENTE
    # =========================================================
    elements.append(Paragraph("DATOS DEL CLIENTE", seccion))

    filas_cliente = [
        [Paragraph("Cliente:", etiqueta), Paragraph(cliente.nombre if cliente else "-", normal)],
        [Paragraph("Documento:", etiqueta), Paragraph(_doc_receptor_texto(cliente), normal)],
        [Paragraph("Condición IVA:", etiqueta), Paragraph(
            cliente.condicion_iva.descripcion if cliente and cliente.condicion_iva else "-", normal
        )],
    ]
    if cliente and cliente.direccion:
        filas_cliente.append([Paragraph("Domicilio:", etiqueta), Paragraph(cliente.direccion, normal)])

    tabla_cliente = Table(filas_cliente, colWidths=[30 * mm, 130 * mm])
    tabla_cliente.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COLOR_ACENTO_SUAVE),
        ("BOX", (0, 0), (-1, -1), 0.5, COLOR_ACENTO),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(tabla_cliente)
    elements.append(Spacer(1, 16))

    # =========================================================
    # TABLA DE ITEMS
    # =========================================================
    elements.append(Paragraph("DETALLE", seccion))

    data = [["Código", "Descripción", "Cant.", "P. Unitario", "Subtotal"]]
    for item in factura.items:
        producto = item.producto
        data.append([
            producto.cod_interno if producto else "-",
            item.descripcion,
            f"{item.cantidad:g}",
            f"$ {item.precio_unitario:,.2f}",
            f"$ {item.subtotal:,.2f}",
        ])

    tabla_items = Table(
        data,
        colWidths=[25 * mm, 70 * mm, 15 * mm, 30 * mm, 30 * mm],
        repeatRows=1,
    )
    estilo_items = [
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_ACENTO),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
        ("ALIGN", (0, 0), (1, -1), "LEFT"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#c7cbd1")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    for i in range(1, len(data)):
        if i % 2 == 0:
            estilo_items.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#f5f6f8")))
    tabla_items.setStyle(TableStyle(estilo_items))

    elements.append(tabla_items)
    elements.append(Spacer(1, 12))

    # =========================================================
    # TOTALES
    # =========================================================
    elements.append(Paragraph(f"TOTAL: $ {float(factura.total):,.2f}", total_style))
    if tipo and tipo.letra in ("B", "C"):
        elements.append(Paragraph("El IVA está incluido en los precios (no se discrimina).", normal_suave))
    elements.append(Spacer(1, 20))
    elements.append(HRFlowable(width="100%", thickness=1, color=COLOR_ACENTO))
    elements.append(Spacer(1, 12))

    # =========================================================
    # CAE + QR
    # =========================================================
    if factura.arca_cae:
        qr_url = construir_url_qr_afip(factura, empresa)
        info_cae = [
            Paragraph("<b>COMPROBANTE AUTORIZADO</b>", normal),
            Spacer(1, 4),
            Paragraph(f"CAE N°: {factura.arca_cae}", normal),
            Paragraph(
                f"Vencimiento CAE: {factura.arca_cae_vto.isoformat() if factura.arca_cae_vto else '-'}",
                normal
            ),
        ]
        pie_tabla = Table(
            [[info_cae, _qr_drawing(qr_url)]],
            colWidths=[110 * mm, 35 * mm],
        )
        pie_tabla.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ]))
        elements.append(pie_tabla)
    else:
        elements.append(Paragraph("Comprobante pendiente de autorización ante AFIP.", normal_suave))

    doc.build(elements)

    pdf = buffer.getvalue()
    buffer.close()

    return pdf
