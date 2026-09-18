import io
import os
import html
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def procesar_imagen_firma(file_obj, width=130, height=40):
    if file_obj is None:
        return ""
    try:
        if hasattr(file_obj, "seek"):
            file_obj.seek(0)
        content = file_obj.read()
        if hasattr(file_obj, "seek"):
            file_obj.seek(0)
        if content and len(content) > 0:
            return Image(io.BytesIO(content), width=width, height=height)
    except Exception as e:
        print(f"Error cargando imagen: {e}")
    return ""

def esc(valor):
    """Función de apoyo para escapar texto de forma segura para ReportLab."""
    if valor is None:
        return ""
    return html.escape(str(valor))

def generar_pdf_hc(datos_hc, plan_tratamiento, evoluciones, firma_paciente_file=None, firma_odonto_file=None):
    buffer = io.BytesIO()
    
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=30,
        bottomMargin=30
    )

    styles = getSampleStyleSheet()
    
    PRIMARY_COLOR = colors.HexColor("#0f766e")
    SECONDARY_COLOR = colors.HexColor("#0284c7")
    NEUTRAL_DARK = colors.HexColor("#0f172a")
    NEUTRAL_LIGHT = colors.HexColor("#f8fafc")
    BORDER_COLOR = colors.HexColor("#cbd5e1")

    title_style = ParagraphStyle(
        'DocTitle', parent=styles['Heading1'], fontSize=11, leading=13, textColor=PRIMARY_COLOR, fontName='Helvetica-Bold'
    )
    header_sub_style = ParagraphStyle(
        'HeaderSub', parent=styles['Normal'], fontSize=8, leading=10, textColor=colors.HexColor("#475569")
    )
    section_title_style = ParagraphStyle(
        'SecTitle', parent=styles['Heading2'], fontSize=9, leading=11, textColor=colors.white, backColor=PRIMARY_COLOR, borderPadding=(3, 4, 3, 4), spaceBefore=6, spaceAfter=4, fontName='Helvetica-Bold'
    )
    body_style = ParagraphStyle('BodyDark', parent=styles['Normal'], fontSize=8, leading=10.5, textColor=NEUTRAL_DARK)
    body_bold = ParagraphStyle('BodyDarkBold', parent=body_style, fontName='Helvetica-Bold')

    cons_title_style = ParagraphStyle(
        'ConsTitle', parent=styles['Heading1'], fontSize=10.5, leading=12, textColor=colors.black, fontName='Helvetica-Bold', alignment=0
    )
    cons_body_style = ParagraphStyle(
        'ConsBody', parent=styles['Normal'], fontSize=8, leading=10.5, textColor=colors.black, fontName='Helvetica'
    )

    story = []

    img_pac = procesar_imagen_firma(firma_paciente_file, width=120, height=35)
    img_odo = procesar_imagen_firma(firma_odonto_file, width=120, height=35)

    # =========================================================================
    # 1. HISTORIA CLÍNICA GENERAL
    # =========================================================================
    header_data = [
        [
            Paragraph("<b>ESCUELA DE SALUD SAN PEDRO CLAVER</b>", title_style),
            Paragraph(f"<b>HISTORIA CLÍNICA N°:</b> {esc(datos_hc.get('Historia Clínica N°', 'HC-2026-001'))}", ParagraphStyle('HCNum', parent=title_style, fontSize=9.5, alignment=2))
        ],
        [
            Paragraph("Sede Neiva — Programa Técnico en Salud Oral", header_sub_style),
            Paragraph(f"<b>Fecha de Atención:</b> {esc(datos_hc.get('Fecha de Atención', ''))}", header_sub_style)
        ]
    ]
    t_header = Table(header_data, colWidths=[340, 200])
    t_header.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('ALIGN', (1,0), (1,1), 'RIGHT')]))
    story.append(t_header)
    story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY_COLOR, spaceBefore=2, spaceAfter=4))

    # DATOS IDENTIFICACIÓN
    story.append(Paragraph("1. DATOS DE IDENTIFICACIÓN DEL PACIENTE", section_title_style))
    datos_paciente = [
        [Paragraph(f"<b>Paciente:</b> {esc(datos_hc.get('Paciente', ''))}", body_style), Paragraph(f"<b>Documento:</b> {esc(datos_hc.get('Tipo Doc', ''))}-{esc(datos_hc.get('Documento Paciente', ''))}", body_style), Paragraph(f"<b>Edad:</b> {esc(datos_hc.get('Edad', ''))} años", body_style)],
        [Paragraph(f"<b>Fecha Nac:</b> {esc(datos_hc.get('Fecha Nacimiento', ''))}", body_style), Paragraph(f"<b>Sexo:</b> {esc(datos_hc.get('Sexo', ''))}", body_style), Paragraph(f"<b>Estado Civil:</b> {esc(datos_hc.get('Estado Civil', ''))}", body_style)],
        [Paragraph(f"<b>Teléfono:</b> {esc(datos_hc.get('Teléfono', ''))}", body_style), Paragraph(f"<b>Dirección:</b> {esc(datos_hc.get('Dirección', ''))}", body_style), Paragraph(f"<b>Ciudad:</b> {esc(datos_hc.get('Ciudad/Departamento', ''))}", body_style)],
        [Paragraph(f"<b>EPS:</b> {esc(datos_hc.get('EPS', ''))}", body_style), Paragraph(f"<b>Ocupación:</b> {esc(datos_hc.get('Ocupación', ''))}", body_style), Paragraph(f"<b>Plan/Condición:</b> {esc(datos_hc.get('Tipo Plan', ''))} / {esc(datos_hc.get('Condición Usuario', ''))}", body_style)]
    ]
    t_paciente = Table(datos_paciente, colWidths=[190, 190, 160])
    t_paciente.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), NEUTRAL_LIGHT), ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR), ('TOPPADDING', (0,0), (-1,-1), 2), ('BOTTOMPADDING', (0,0), (-1,-1), 2)]))
    story.append(t_paciente)

    # ANAMNESIS
    story.append(Paragraph("2. ANAMNESIS Y EXAMEN FÍSICO ESTOMATOLÓGICO", section_title_style))
    story.append(Paragraph(f"<b>Motivo de Consulta:</b> {esc(datos_hc.get('Motivo de Consulta', 'Sin registrar'))}", body_style))
    story.append(Paragraph(f"<b>Enfermedad Actual:</b> {esc(datos_hc.get('Enfermedad Actual', 'No refiere'))}", body_style))
    story.append(Paragraph(f"<b>Higiene Oral:</b> {esc(datos_hc.get('Higiene Oral', ''))}", body_style))
    story.append(Paragraph(f"<b>Examen Dental / Periodontal:</b> {esc(datos_hc.get('Dental', ''))} | {esc(datos_hc.get('Periodontal', ''))}", body_style))

    # DIAGNÓSTICOS Y PLAN
    story.append(Paragraph("3. DIAGNÓSTICOS Y PLAN DE TRATAMIENTO", section_title_style))
    story.append(Paragraph(f"<b>Diagnósticos (CIE-10):</b> {esc(datos_hc.get('Diags', 'Sin registro'))}", body_style))
    story.append(Paragraph(f"<b>Plan de Tratamiento:</b> {esc(datos_hc.get('Plan Resumen', 'No especificado'))}", body_style))

    if plan_tratamiento:
        story.append(Spacer(1, 3))
        table_odonto_data = [["Pieza (FDI)", "Hallazgo / Convención", "Superficie", "Observación"]]
        for item in plan_tratamiento:
            table_odonto_data.append([
                esc(item.get("Diente", "")), 
                esc(item.get("Hallazgo", "")), 
                esc(item.get("Superficies", "N/A")), 
                esc(item.get("Observación", ""))
            ])
        t_odonto = Table(table_odonto_data, colWidths=[70, 150, 110, 210])
        t_odonto.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), SECONDARY_COLOR), ('TEXTCOLOR', (0,0), (-1,0), colors.white), ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR), ('TOPPADDING', (0,0), (-1,-1), 1.5), ('BOTTOMPADDING', (0,0), (-1,-1), 1.5)]))
        story.append(t_odonto)

    # EVOLUCIÓN (Protegida con esc())
    story.append(Paragraph("4. REGISTRO DE EVOLUCIÓN CLÍNICA", section_title_style))
    if evoluciones:
        evo_data = [["Fecha", "Diente/Sitio", "Tratamiento Ejecutado"]]
        for ev in evoluciones:
            evo_data.append([
                esc(ev.get("Fecha y Hora", "")), 
                esc(ev.get("Diente/Sitio", "")), 
                esc(ev.get("Tratamiento Ejecutado", ""))
            ])
        t_evo = Table(evo_data, colWidths=[90, 110, 340])
        t_evo.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), PRIMARY_COLOR), ('TEXTCOLOR', (0,0), (-1,0), colors.white), ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR), ('TOPPADDING', (0,0), (-1,-1), 2), ('BOTTOMPADDING', (0,0), (-1,-1), 2)]))
        story.append(t_evo)
    else:
        story.append(Paragraph("Sin novedades registradas en esta consulta.", body_style))

    # FIRMAS OBLIGATORIAS
    story.append(Spacer(1, 15))
    story.append(Paragraph("5. CONSTANCIA Y FIRMAS DE CONFORMIDAD", section_title_style))
    story.append(Spacer(1, 10))

    firmas_hc_data = [
        [img_pac if img_pac != "" else Paragraph("", body_style), img_odo if img_odo != "" else Paragraph("", body_style)],
        ["_______________________________________", "_______________________________________"],
        [
            Paragraph(f"<b>Paciente / Acudiente:</b><br/>{esc(datos_hc.get('Paciente', ''))}<br/>Doc: {esc(datos_hc.get('Tipo Doc', ''))} {esc(datos_hc.get('Documento Paciente', ''))}", body_style),
            Paragraph(f"<b>Odontólogo / Estudiante:</b><br/>{esc(datos_hc.get('Odontólogo Tratante', ''))}<br/>Reg: {esc(datos_hc.get('Código/Registro', ''))}", body_style)
        ]
    ]
    t_firmas_hc = Table(firmas_hc_data, colWidths=[270, 270])
    t_firmas_hc.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER'), ('VALIGN', (0,0), (-1,-1), 'BOTTOM')]))
    story.append(t_firmas_hc)

    # =========================================================================
    # 2. ANEXO DE CONSENTIMIENTO
    # =========================================================================
    tipo_cons = datos_hc.get("Consentimiento Tipo", "Ninguno / No aplica para esta consulta")

    if tipo_cons and "Ninguno" not in tipo_cons:
        story.append(PageBreak())
        
        img_logo = ""
        if os.path.exists("logo.png"):
            try:
                img_logo = Image("logo.png", width=110, height=45)
            except Exception:
                img_logo = Paragraph("<b>ESCUELA SAN PEDRO CLAVER</b>", body_bold)

        if "Raspaje" in tipo_cons:
            head_cons = [[Paragraph("<b>CONSENTIMIENTO INFORMADO PARA RASPAJE SUPRAGINGIVAL</b>", cons_title_style), img_logo]]
            t_head_c = Table(head_cons, colWidths=[410, 130])
            t_head_c.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('ALIGN', (1,0), (1,0), 'RIGHT')]))
            story.append(t_head_c)
            story.append(Spacer(1, 4))

            texto_exacto = """
            <b>Apreciado(a) paciente:</b><br/>
            Antes de realizar cualquier procedimiento, es importante que conozca en qué consiste, cuáles son sus beneficios, riesgos y alternativas. Lea atentamente la siguiente información.<br/>
            Si tiene dudas, consulte con su profesional tratante antes de firmar este consentimiento.<br/><br/>
            <b>1. DESCRIPCIÓN DEL PROCEDIMIENTO</b><br/>
            El raspaje supragingival o raspado dental es un procedimiento mediante el cual se eliminan de forma mecánica los depósitos calcificados de placa bacteriana, conocidos como cálculos dentales o sarro, que se acumulan en la superficie de los dientes y alrededor del cuello de los mismos.<br/>
            Para su realización se emplean instrumentos manuales, sónicos o ultrasónicos.<br/>
            Este procedimiento suele realizarse con una frecuencia aproximada de <b>1 a 2 veces por año</b>, según la necesidad de cada paciente.<br/><br/>
            <b>2. OBJETIVOS DEL PROCEDIMIENTO</b><br/>
            • Prevenir enfermedades de las encías y tejidos de soporte dental.<br/>
            • Mantener una adecuada salud bucal.<br/>
            • Favorecer la estética y el bienestar oral.<br/><br/>
            <b>3. BENEFICIOS ESPERADOS</b><br/>
            • Eliminación de la placa bacteriana y el cálculo dental.<br/>
            • Disminución del mal aliento (halitosis).<br/>
            • Prevención de la gingivitis y periodontitis.<br/>
            • Sensación de limpieza y frescura en la boca<br/><br/>
            <b>4. RIESGOS DEL PROCEDIMIENTO</b><br/>
            Aunque es un procedimiento seguro, puede presentarse:<br/>
            • Sensibilidad dental temporal al frío o calor.<br/>
            • Pequeños sangrados de encías durante o después del procedimiento.<br/>
            • Molestias leves o irritación gingival pasajera.<br/>
            • En casos excepcionales, daño menor a los tejidos blandos.<br/><br/>
            <b>5. RIESGOS DE NO REALIZAR EL PROCEDIMIENTO</b><br/>
            La falta de raspaje puede causar acumulación de placa y calculo, lo que incrementa el riesgo de gingivitis, periodontitis, movilidad y posible pérdida de los dientes con el tiempo.<br/><br/>
            <b>6. INFORMACIÓN ADICIONAL</b><br/>
            Usted puede realizar preguntas y aclarar cualquier duda antes, durante o después del procedimiento.<br/>
            Tiene derecho a retirar su consentimiento en cualquier momento, sin que esto afecte la atención futura que pueda recibir.<br/><br/>
            <b>He leído y comprendido la información anterior.</b><br/>
            <b>Autorizo de manera libre y voluntaria la realización del procedimiento de raspaje supragingival.</b>
            """
            story.append(Paragraph(texto_exacto, cons_body_style))
            story.append(Spacer(1, 6))

            datos_pie = [
                [Paragraph(f"<b>Nombre del paciente:</b> {esc(datos_hc.get('Paciente', ''))}", cons_body_style), img_pac if img_pac != "" else Paragraph("", body_style)],
                [Paragraph(f"<b>Documento de identidad:</b> {esc(datos_hc.get('Tipo Doc', ''))} {esc(datos_hc.get('Documento Paciente', ''))}", cons_body_style), Paragraph("___________________________________", cons_body_style)],
                [Paragraph(f"<b>Firma del paciente:</b>", cons_body_style), Paragraph("", cons_body_style)],
                [Paragraph(f"<b>Fecha atención:</b> {esc(datos_hc.get('Fecha de Atención', ''))}", cons_body_style), img_odo if img_odo != "" else Paragraph("", body_style)],
                [Paragraph(f"<b>Nombre del estudiante:</b> {esc(datos_hc.get('Odontólogo Tratante', ''))}", cons_body_style), Paragraph("___________________________________", cons_body_style)],
                [Paragraph(f"<b>Firma del estudiante:</b>", cons_body_style), Paragraph("", cons_body_style)]
            ]
            t_pie = Table(datos_pie, colWidths=[320, 220])
            t_pie.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'BOTTOM'), ('TOPPADDING', (0,0), (-1,-1), 1), ('BOTTOMPADDING', (0,0), (-1,-1), 1)]))
            story.append(t_pie)

        elif "Higiene Oral" in tipo_cons:
            head_cons = [[Paragraph("<b>CONSENTIMIENTO INFORMADO PARA HIGIENE ORAL</b>", cons_title_style), img_logo]]
            t_head_c = Table(head_cons, colWidths=[410, 130])
            t_head_c.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('ALIGN', (1,0), (1,0), 'RIGHT')]))
            story.append(t_head_c)
            story.append(Spacer(1, 6))

            info_top = [
                [Paragraph(f"<b>Nombre y Apellido del Paciente:</b> {esc(datos_hc.get('Paciente', ''))}", cons_body_style)],
                [Paragraph(f"<b>Documento identidad:</b> {esc(datos_hc.get('Tipo Doc', ''))} {esc(datos_hc.get('Documento Paciente', ''))}", cons_body_style)],
                [Paragraph(f"<b>Edad:</b> {esc(datos_hc.get('Edad', ''))} años", cons_body_style)],
                [Paragraph(f"<b>Fecha atención:</b> {esc(datos_hc.get('Fecha de Atención', ''))}", cons_body_style)]
            ]
            t_top = Table(info_top, colWidths=[540])
            t_top.setStyle(TableStyle([('TOPPADDING', (0,0), (-1,-1), 1), ('BOTTOMPADDING', (0,0), (-1,-1), 1)]))
            story.append(t_top)
            story.append(Spacer(1, 8))

            texto_ho = """
            Por medio del presente documento, se autoriza al higienista oral de la <b>Escuela de Salud San Pedro Claver</b> para realizar el procedimiento de higiene oral.<br/><br/>
            El paciente ha sido informado de que este procedimiento consiste en la eliminación de placa bacteriana, manchas y cálculos superficiales mediante el uso de instrumentos manuales y/o mecánicos, con el fin de mejorar la salud bucal y prevenir enfermedades orales como la gingivitis y la periodontitis.<br/><br/>
            También se ha informado sobre los posibles efectos secundarios o molestias que pueden presentarse durante o después del procedimiento, tales como:<br/>
            • Sensibilidad dental transitoria con estímulos fríos o calientes.<br/>
            • Sangrado o irritación leve en las encías.<br/>
            • Inflamación o enrojecimiento gingival pasajero.<br/>
            • Molestias al masticar o al cepillarse durante las primeras horas posteriores a la atención.<br/><br/>
            De igual forma, se ha explicado que, en algunos casos, puede ser necesario remitir al paciente a un odontólogo para valoración o toma de radiografías si se evidencian alteraciones que lo requieran.<br/><br/>
            <b>El paciente declara haber recibido la información completa sobre el procedimiento, sus beneficios, riesgos y cuidados posteriores, y manifiesta estar de acuerdo con su realización.</b>
            """
            story.append(Paragraph(texto_ho, cons_body_style))
            story.append(Spacer(1, 25))

            firmas_ho = [
                [img_pac if img_pac != "" else Paragraph("", body_style), img_odo if img_odo != "" else Paragraph("", body_style)],
                ["_______________________________________", "_______________________________________"],
                [
                    Paragraph(f"<b>Firma del paciente</b><br/>{esc(datos_hc.get('Paciente', ''))}", cons_body_style),
                    Paragraph(f"<b>Firma del higienista oral</b><br/>{esc(datos_hc.get('Odontólogo Tratante', ''))}", cons_body_style)
                ]
            ]
            t_f_ho = Table(firmas_ho, colWidths=[270, 270])
            t_f_ho.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER'), ('VALIGN', (0,0), (-1,-1), 'BOTTOM')]))
            story.append(t_f_ho)

        else:
            head_cons = [[Paragraph("<b>CONSENTIMIENTO INFORMADO PARA APLICACIÓN DE FLUOR</b>", cons_title_style), img_logo]]
            t_head_c = Table(head_cons, colWidths=[410, 130])
            t_head_c.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('ALIGN', (1,0), (1,0), 'RIGHT')]))
            story.append(t_head_c)
            story.append(Spacer(1, 6))

            info_top = [
                [Paragraph(f"<b>Nombre y apellido del paciente:</b> {esc(datos_hc.get('Paciente', ''))}", cons_body_style), Paragraph(f"<b>Edad:</b> {esc(datos_hc.get('Edad', ''))} años", cons_body_style)],
                [Paragraph(f"<b>Número de identificación:</b> {esc(datos_hc.get('Tipo Doc', ''))} {esc(datos_hc.get('Documento Paciente', ''))}", cons_body_style), Paragraph(f"<b>Fecha aplicación:</b> {esc(datos_hc.get('Fecha de Atención', ''))}", cons_body_style)]
            ]
            t_top = Table(info_top, colWidths=[360, 180])
            t_top.setStyle(TableStyle([('TOPPADDING', (0,0), (-1,-1), 1), ('BOTTOMPADDING', (0,0), (-1,-1), 1)]))
            story.append(t_top)
            story.append(Spacer(1, 6))

            texto_fl = f"""
            <b>Apreciado(a) paciente:</b><br/>
            Antes de realizar cualquier procedimiento, es importante que conozca en qué consiste, cuáles son sus beneficios, riesgos y alternativas. Lea atentamente la siguiente información.<br/>
            Si tiene dudas, consulte con su profesional tratante antes de firmar este consentimiento<br/><br/>
            Se entiende por <b>APLICACIÓN DE FLUOR BARNIZ</b> el procedimiento preventivo para caries dental y terapéutica para la detección temprana, mediante la aplicación del flúor barniz en las superficies dentarias. Actividad que busca retardar y detener el proceso de caries dental, al poner en contacto la parte coronal o radicular del diente con un vehículo que contiene altas concentraciones de flúor, pero que por su secado rápido al entrar en contacto con la saliva permite la formación de una película que libera de forma lenta y continua iones de fluoruro hacia la superficie del diente subyacente cubriendo el esmalte dental, para reducir su desmineralización y disolución por la acción de microorganismos y la producción de ácidos que se acumulan durante la formación de biofilm y de la placa dental.<br/><br/>
            Los niños, niñas y jóvenes entre 1 y 17 años, son la población objeto para la aplicación del flúor barniz, incluida en el Plan de beneficios en salud, con una frecuencia de aplicación mínima de dos veces por año, teniendo en cuenta la valoración del riesgo individual y que entre aplicación y aplicación debe existir un periodo de 6 meses, dada la liberación prolongada de flúor.<br/><br/>
            Certifico que el odontólogo o higienista, éste último bajo la supervisión del odontólogo, me ha explicado el procedimiento a realizar y los cuidados que debo tener posteriormente.<br/>
            Igualmente certifico que me han explicado la importancia de continuar con su aplicación según la valoración de riesgo registrada, para asistir a la próxima aplicación y cumplir con lo acordado durante el año, solicitado por el odontólogo o higienista oral, personal autorizado(s) y capacitado(s) para dichas aplicaciones.<br/><br/>
            He tenido la oportunidad de hacer las preguntas que he considerado necesarias y todas han sido contestadas satisfactoriamente; así como se me ha explicado que, debido al color del barniz, puede presentarse un leve cambio temporal en el color del diente, que el periodo de tratamiento es de 4 horas (debo evitar los alimentos duros o pegajosos, productos con alcohol, enjuagues, bebidas calientes o lavarme los dientes por estas 4 horas) siguientes a la aplicación del barniz y preferiblemente realizar el cepillado dental hasta la mañana siguiente.<br/><br/>
            <b>Fecha de próxima aplicación:</b> {esc(datos_hc.get('Proxima Cita Fluor', 'N/A'))}
            """
            story.append(Paragraph(texto_fl, cons_body_style))
            story.append(Spacer(1, 20))

            firmas_fl = [
                [img_pac if img_pac != "" else Paragraph("", body_style), img_odo if img_odo != "" else Paragraph("", body_style)],
                ["_______________________________________", "_______________________________________"],
                [
                    Paragraph("<b>Firma de paciente y/o acompañante</b>", cons_body_style),
                    Paragraph("<b>Firma de higienista oral</b>", cons_body_style)
                ]
            ]
            t_f_fl = Table(firmas_fl, colWidths=[270, 270])
            t_f_fl.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER'), ('VALIGN', (0,0), (-1,-1), 'BOTTOM')]))
            story.append(t_f_fl)

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()