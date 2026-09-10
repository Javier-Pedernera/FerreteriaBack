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


def _datos_receptor(factura):
    """Mismo criterio que arca_service.wsfe_autorizar para DocTipo/DocNro."""
    cliente = factura.cliente
    if cliente:
        if not cliente.tipo_documento:
            return 99, 0
        doc_tipo = cliente.tipo_documento.codigo_afip
        if doc_tipo == 99 or not cliente.cuit:
            return doc_tipo, 0
        return doc_tipo, int(cliente.cuit)

    # sin cliente registrado
    doc_tipo = factura.receptor_doc_tipo or 99
    if doc_tipo == 99 or not factura.receptor_doc_nro:
        return doc_tipo, 0
    return doc_tipo, int(factura.receptor_doc_nro)


def construir_url_qr_afip(factura, empresa):
    """
    Arma la URL del QR exigido por AFIP (RG 4892) para comprobantes
    electrónicos: https://www.afip.gob.ar/fe/qr/?p=<json en base64>
    """
    doc_tipo, doc_nro = _datos_receptor(factura)

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


DOC_TIPO_LABEL = {80: "CUIT", 86: "CUIL", 96: "DNI", 94: "Pasaporte", 99: "Consumidor Final"}
COND_IVA_RECEPTOR_LABEL = {
    1: "Responsable Inscripto", 4: "Sujeto Exento", 5: "Consumidor Final",
    6: "Responsable Monotributo", 7: "Sujeto No Categorizado",
}


def _doc_receptor_texto(factura):
    cliente = factura.cliente
    if cliente:
        if not cliente.tipo_documento or cliente.tipo_documento.codigo_afip == 99:
            return "—"
        return f"{cliente.tipo_documento.descripcion}: {cliente.cuit or '—'}"

    doc_tipo = factura.receptor_doc_tipo or 99
    if doc_tipo == 99:
        return "—"
    return f"{DOC_TIPO_LABEL.get(doc_tipo, doc_tipo)}: {factura.receptor_doc_nro or '—'}"


def _fmt_fecha(d):
    if not d:
        return "-"
    return d.strftime("%d/%m/%Y")


def _fmt_pesos(v):
    return f"$ {float(v or 0):,.2f}".replace(",", "@").replace(".", ",").replace("@", ".")


def _condicion_venta(factura):
    """Forma de pago de las ventas facturadas."""
    formas = {v.forma_pago.nombre for v in factura.ventas if getattr(v, "forma_pago", None)}
    if len(formas) == 1:
        return formas.pop()
    if len(formas) > 1:
        return "Varios"
    return "Contado"


def _numerar_pagina(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(COLOR_TEXTO_SUAVE)
    canvas.drawRightString(
        doc.pagesize[0] - 25 * mm, 12 * mm, f"Página {doc.page}"
    )
    canvas.restoreState()


def generar_pdf_factura(factura):
    """
    Genera el PDF de una Factura real (modelo app.models.factura.Factura),
    con formato de factura electrónica argentina.
    """
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=25 * mm,
        leftMargin=25 * mm,
        topMargin=14 * mm,
        bottomMargin=18 * mm,
        title=f"Factura {factura.numero_comprobante or factura.id}",
    )

    ancho = doc.width  # ancho útil de contenido

    base = getSampleStyleSheet()
    normal = ParagraphStyle("n", parent=base["Normal"], fontSize=8.5, leading=12)
    suave = ParagraphStyle("s", parent=normal, textColor=COLOR_TEXTO_SUAVE)
    mini = ParagraphStyle("m", parent=normal, fontSize=7.5, textColor=COLOR_TEXTO_SUAVE)
    etiqueta = ParagraphStyle("e", parent=normal, fontSize=7.5, textColor=COLOR_TEXTO_SUAVE)
    nombre_style = ParagraphStyle("nom", parent=base["Heading2"], fontSize=15, leading=17)
    seccion = ParagraphStyle(
        "sec", parent=base["Heading5"], fontSize=8.5, textColor=colors.white,
        leading=11, spaceAfter=0, spaceBefore=0,
    )
    centro = ParagraphStyle("c", parent=normal, alignment=TA_CENTER, fontSize=6.5)
    letra_style = ParagraphStyle("l", parent=base["Title"], fontSize=24, alignment=TA_CENTER, leading=26)
    original_style = ParagraphStyle("o", parent=normal, alignment=TA_CENTER, fontSize=6, textColor=COLOR_TEXTO_SUAVE)
    comp_title = ParagraphStyle("ct", parent=base["Heading2"], fontSize=11, leading=13)
    comp_line = ParagraphStyle("cl", parent=normal, fontSize=7.5, leading=10)
    total_lbl = ParagraphStyle("tl", parent=base["Heading3"], fontSize=13, alignment=TA_RIGHT)

    try:
        empresa = EmpresaFiscalService.get_empresa_activa()
    except ValueError:
        empresa = None

    cliente = factura.cliente
    tipo = factura.tipo_comprobante

    pv_num = factura.punto_venta_emitido or (
        factura.punto_venta.numero if factura.punto_venta else None
    )
    numero_fmt = formatear_numero(pv_num, factura.arca_numero_cbte)
    fecha = factura.fecha_emision or (
        factura.fecha_creacion.date() if factura.fecha_creacion else None
    )
    codigo_afip = tipo.codigo_afip if tipo else factura.arca_tipo_cbte
    domicilio_emisor = (empresa.domicilio if empresa and empresa.domicilio else None) or (
        factura.punto_venta.direccion if factura.punto_venta else None
    )

    elements = []

    # =========================================================
    # ENCABEZADO — 3 columnas: emisor | recuadro letra | comprobante
    # =========================================================
    logo_img = _logo_flowable(empresa.logo_url if empresa else None)

    razon_social = empresa.razon_social if empresa else "-"
    col_emisor = []
    if logo_img:
        # Con logo, la identidad visual la da el logo: no repetimos el nombre
        # en grande, solo la razón social como dato legal obligatorio.
        col_emisor += [logo_img, Spacer(1, 6)]
        col_emisor.append(Paragraph(f"Razón social: {razon_social}", normal))
    else:
        col_emisor.append(Paragraph(
            (empresa.nombre_fantasia or razon_social) if empresa else "-", nombre_style
        ))
        if empresa and empresa.nombre_fantasia and empresa.nombre_fantasia != razon_social:
            col_emisor.append(Paragraph(f"Razón social: {razon_social}", normal))
    col_emisor.append(Paragraph(
        f"Condición frente al IVA: {empresa.condicion_iva.descripcion if empresa and empresa.condicion_iva else '-'}",
        normal
    ))
    if domicilio_emisor:
        col_emisor.append(Paragraph(f"Domicilio comercial: {domicilio_emisor}", normal))

    col_letra = Table(
        [
            [Paragraph("ORIGINAL", original_style)],
            [Paragraph(tipo.letra if tipo else "-", letra_style)],
            [Paragraph(f"COD. {codigo_afip:03d}" if codigo_afip else "-", centro)],
        ],
        colWidths=[18 * mm],
    )
    col_letra.setStyle(TableStyle([
        ("BOX", (0, 1), (-1, -1), 1, COLOR_ACENTO),
        ("LINEBELOW", (0, 1), (-1, 1), 0.8, COLOR_ACENTO),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))

    col_comp = [
        Paragraph(f"<b>{(tipo.descripcion if tipo else 'COMPROBANTE').upper()}</b>", comp_title),
        Spacer(1, 3),
        Paragraph(f"<b>N°:</b> {numero_fmt}", comp_line),
        Paragraph(f"<b>Fecha de emisión:</b> {_fmt_fecha(fecha)}", comp_line),
        Spacer(1, 3),
        Paragraph(f"<b>CUIT:</b> {empresa.cuit if empresa else '-'}", comp_line),
    ]
    if empresa and empresa.ingresos_brutos:
        col_comp.append(Paragraph(f"<b>Ingresos Brutos:</b> {empresa.ingresos_brutos}", comp_line))
    if empresa and empresa.inicio_actividades:
        col_comp.append(Paragraph(
            f"<b>Inicio de actividades:</b> {_fmt_fecha(empresa.inicio_actividades)}", comp_line
        ))

    w1 = ancho * 0.42
    w2 = 26 * mm
    header = Table([[col_emisor, col_letra, col_comp]], colWidths=[w1, w2, ancho - w1 - w2])
    header.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (1, 0), (1, 0), "CENTER"),
        ("LINEAFTER", (0, 0), (0, 0), 0.6, COLOR_TEXTO_SUAVE),
        ("LEFTPADDING", (1, 0), (1, 0), 8),
        ("RIGHTPADDING", (1, 0), (1, 0), 8),
        ("LEFTPADDING", (2, 0), (2, 0), 10),
    ]))
    elements += [header, Spacer(1, 8),
                 HRFlowable(width="100%", thickness=1.2, color=COLOR_ACENTO), Spacer(1, 10)]

    # =========================================================
    # DATOS DEL RECEPTOR
    # =========================================================
    def barra_seccion(texto):
        t = Table([[Paragraph(texto, seccion)]], colWidths=[ancho])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), COLOR_ACENTO),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        return t

    elements += [barra_seccion("DATOS DEL RECEPTOR"), Spacer(1, 6)]

    if cliente and cliente.condicion_iva:
        cond_iva_txt = cliente.condicion_iva.descripcion
    else:
        cond_iva_txt = COND_IVA_RECEPTOR_LABEL.get(
            factura.receptor_condicion_iva or 5, "Consumidor Final"
        )

    filas_rec = [
        [Paragraph("Receptor:", etiqueta), Paragraph(factura.receptor_display(), normal),
         Paragraph("Condición IVA:", etiqueta), Paragraph(cond_iva_txt, normal)],
        [Paragraph("Documento:", etiqueta), Paragraph(_doc_receptor_texto(factura), normal),
         Paragraph("Condición de venta:", etiqueta), Paragraph(_condicion_venta(factura), normal)],
    ]
    if cliente and cliente.direccion:
        filas_rec.append([Paragraph("Domicilio:", etiqueta),
                          Paragraph(cliente.direccion, normal), "", ""])

    tabla_rec = Table(filas_rec, colWidths=[ancho * 0.13, ancho * 0.37, ancho * 0.18, ancho * 0.32])
    tabla_rec.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COLOR_ACENTO_SUAVE),
        ("BOX", (0, 0), (-1, -1), 0.5, COLOR_TEXTO_SUAVE),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    elements += [tabla_rec, Spacer(1, 14)]

    # =========================================================
    # DETALLE
    # =========================================================
    elements += [barra_seccion("DETALLE"), Spacer(1, 6)]

    data = [["Código", "Descripción", "Cant.", "P. Unitario", "Subtotal"]]
    for item in factura.items:
        producto = item.producto
        data.append([
            producto.cod_interno if producto else "-",
            Paragraph(item.descripcion, normal),
            f"{item.cantidad:g}",
            _fmt_pesos(item.precio_unitario),
            _fmt_pesos(item.subtotal),
        ])

    cw = [ancho * 0.16, ancho * 0.44, ancho * 0.10, ancho * 0.15, ancho * 0.15]
    tabla_items = Table(data, colWidths=cw, repeatRows=1)
    estilo = [
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_ACENTO),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
        ("LINEBELOW", (0, 0), (-1, 0), 0.8, COLOR_ACENTO),
        ("LINEBELOW", (0, 1), (-1, -1), 0.4, colors.HexColor("#d6d9de")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]
    for i in range(1, len(data)):
        if i % 2 == 0:
            estilo.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#f6f7f9")))
    tabla_items.setStyle(TableStyle(estilo))
    elements += [tabla_items, Spacer(1, 10)]

    # =========================================================
    # TOTALES — caja a la derecha
    # =========================================================
    filas_total = []
    if tipo and tipo.letra == "A":
        # (para cuando se implemente IVA discriminado)
        filas_total.append(
            [Paragraph("Subtotal", total_lbl), Paragraph(_fmt_pesos(factura.total), total_lbl)]
        )
    filas_total.append(
        [Paragraph("<b>TOTAL</b>", total_lbl), Paragraph(f"<b>{_fmt_pesos(factura.total)}</b>", total_lbl)]
    )
    caja_total = Table(filas_total, colWidths=[ancho * 0.20, ancho * 0.20], hAlign="RIGHT")
    caja_total.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.8, COLOR_ACENTO),
        ("BACKGROUND", (0, -1), (-1, -1), COLOR_ACENTO_SUAVE),
        ("LINEABOVE", (0, -1), (-1, -1), 0.4, colors.HexColor("#d6d9de")),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    elements.append(caja_total)
    if tipo and tipo.letra in ("B", "C"):
        elements += [Spacer(1, 4),
                     Paragraph("Los importes incluyen IVA. Comprobante sin discriminación de IVA "
                               "(Régimen Simplificado / Consumidor Final).", mini)]
    elements.append(Spacer(1, 18))

    # =========================================================
    # PIE — CAE + QR
    # =========================================================
    if factura.arca_cae:
        qr_url = construir_url_qr_afip(factura, empresa)
        info_cae = [
            Paragraph("<b>Comprobante Autorizado</b>", normal),
            Spacer(1, 3),
            Paragraph(f"CAE N°: <b>{factura.arca_cae}</b>", normal),
            Paragraph(f"Vencimiento del CAE: {_fmt_fecha(factura.arca_cae_vto)}", normal),
        ]
        pie = Table([[_qr_drawing(qr_url, 30 * mm), info_cae]], colWidths=[34 * mm, ancho - 34 * mm])
        pie.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BOX", (0, 0), (-1, -1), 0.6, COLOR_TEXTO_SUAVE),
            ("LEFTPADDING", (1, 0), (1, 0), 12),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        elements.append(pie)
    else:
        elements.append(Paragraph("Comprobante pendiente de autorización ante AFIP.", suave))

    doc.build(elements, onFirstPage=_numerar_pagina, onLaterPages=_numerar_pagina)

    pdf = buffer.getvalue()
    buffer.close()
    return pdf
