import streamlit as st
import pandas as pd
from datetime import datetime, date
import os
import base64
from PIL import Image, ImageDraw, ImageFont
from streamlit_image_coordinates import streamlit_image_coordinates
from pdf_generator import generar_pdf_hc

st.set_page_config(
    page_title="Historia Clínica Odontológica - San Pedro Claver",
    page_icon="🦷",
    layout="wide"
)

hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

def cargar_css(file_name):
    if os.path.exists(file_name):
        with open(file_name, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

cargar_css("stilo.css")

# Función para incrustar logo en Base64 si existe
def get_image_base64(path):
    if os.path.exists(path):
        with open(path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    return ""

logo_b64 = get_image_base64("logo.png")
logo_html = f'<img src="data:image/png;base64,{logo_b64}" style="height: 70px; margin-right: 20px;">' if logo_b64 else '🦷 '

st.markdown(f"""
    <div class="header-banner">
        <div style="display: flex; align-items: center;">
            {logo_html}
            <div>
                <h1 class="header-title">HISTORIA CLÍNICA ODONTOLÓGICA</h1>
                <p class="header-subtitle">Escuela de Salud San Pedro Claver — Sede Neiva</p>
            </div>
        </div>
        <div style="text-align: right;">
            <span class="badge-session">SESIÓN ABIERTA</span>
            <p style="color: #ccfbf1; font-size: 11px; margin: 4px 0 0 0;">Diligenciamiento seguro</p>
        </div>
    </div>
""", unsafe_allow_html=True)

st.markdown("""
    <div style="padding: 10px 0; color: #0f766e; font-size: 13px; font-weight: 600;">
        <b>Consulta nueva</b> / Completa los módulos en orden para construir el expediente. &nbsp;&nbsp;|&nbsp;&nbsp; 
        <span style="color: #475569;">Estado: <b style="color: #059669;">En diligenciamiento</b></span>
    </div>
""", unsafe_allow_html=True)

if "evoluciones" not in st.session_state:
    st.session_state.evoluciones = []

if "plan_tratamiento" not in st.session_state:
    st.session_state.plan_tratamiento = []

if "marcas_odontograma" not in st.session_state:
    st.session_state.marcas_odontograma = []

if "convencion_odontograma" not in st.session_state:
    st.session_state.convencion_odontograma = "Caries"

if "odonto_version" not in st.session_state:
    st.session_state.odonto_version = 0

if "ultimo_click_odonto" not in st.session_state:
    st.session_state.ultimo_click_odonto = None

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "1. Datos Administrativos", 
    "2. Anamnesis y Antecedentes", 
    "3. Examen Estomatológico",
    "4. Odontograma y Diag.", 
    "5. Evolución", 
    "6. Firmas y Consentimientos"
])

# --- TAB 1
with tab1:
    st.markdown('<div class="stCardModule">', unsafe_allow_html=True)
    st.markdown('<div><span class="badge-modulo">MÓDULO 0</span><b style="color: #0f172a; font-size: 15px;">Datos Administrativos de la Consulta</b></div><br>', unsafe_allow_html=True)
    c0_1, c0_2, c0_3 = st.columns(3)
    with c0_1:
        hc_num = st.text_input("HISTORIA CLÍNICA N°", value="HC-2026-001", key="input_hc_num")
    with c0_2:
        fecha_hc = st.date_input(
            "FECHA DE ATENCIÓN", 
            value=date.today(),
            min_value=date(2020, 1, 1),
            max_value=date(2030, 12, 31),
            key="input_fecha_hc"
        )
    with c0_3:
        eps = st.text_input("EPS DEL PACIENTE", value="", placeholder="Escribe la EPS...", key="input_eps")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="stCardModule">', unsafe_allow_html=True)
    st.markdown('<div><span class="badge-modulo">MÓDULO 1</span><b style="color: #0f172a; font-size: 15px;">Datos Personales del Paciente</b></div><br>', unsafe_allow_html=True)
    st.markdown('<span class="subseccion-titulo">➖ IDENTIFICACIÓN E INFORMACIÓN GENERAL</span><br><br>', unsafe_allow_html=True)

    c1_1, c1_2, c1_3 = st.columns(3)
    with c1_1:
        nombre_paciente = st.text_input("Nombre del Paciente (Completo)", value="", placeholder="Nombre completo...", key="input_nombre")
        tipo_doc = st.selectbox("Tipo de Documento", ["Seleccione...", "CC", "TI", "RC", "MS", "CE", "PA", "ASI"], key="input_tipodoc")
        sexo = st.radio("Sexo", ["Hombre", "Mujer"], index=None, horizontal=True, key="input_sexo")
        tipo_plan = st.selectbox("Tipo de Plan", ["Seleccione...", "POS", "POS SUBS.", "PREPAGO", "OTRO"], key="input_tipplan")

    with c1_2:
        num_doc = st.text_input("N° de Documento", value="", placeholder="Número de documento...", key="input_numdoc")
        fecha_nac = st.date_input(
            "Fecha de Nacimiento", 
            value=date(2000, 1, 1),
            min_value=date(1920, 1, 1),
            max_value=date.today(),
            key="input_fechanac"
        )
        edad = st.number_input("Edad (Años)", min_value=0, max_value=120, value=0, key="input_edad")
        condicion_usuario = st.selectbox("Condición del Usuario", ["Seleccione...", "COTIZANTE", "BENEFICIARIO", "PENSIONADO", "OTRO"], key="input_condicion")

    with c1_3:
        direccion = st.text_input("Dirección de Vivienda", value="", placeholder="Dirección...", key="input_dir")
        telefono = st.text_input("Teléfono de Contacto", value="", placeholder="Teléfono...", key="input_tel")
        
        lista_ciudades = [
            "Neiva / Huila",
            "Bogotá D.C.",
            "Medellín / Antioquia",
            "Cali / Valle del Cauca",
            "Barranquilla / Atlántico",
            "Cartagena / Bolívar",
            "Bucaramanga / Santander",
            "Ibagué / Tolima",
            "Villavicencio / Meta",
            "Florencia / Caquetá",
            "Garzón / Huila",
            "Pitalito / Huila",
            "La Plata / Huila",
            "Otro / Fuera de Colombia"
        ]
        ciudad_depto = st.selectbox("Ciudad / Departamento", lista_ciudades, key="input_ciudad")
        
        estado_civil = st.selectbox("Estado Civil", ["Seleccione...", "Soltero", "Casado", "Otro"], key="input_estcivil")
        ocupacion = st.text_input("Ocupación", value="", placeholder="Ocupación...", key="input_ocupacion")

    st.markdown('<span class="subseccion-titulo">➖ ACOMPAÑANTE Y RESPONSABLE</span><br><br>', unsafe_allow_html=True)
    c1_4, c1_5 = st.columns(2)
    with c1_4:
        nombre_acomp = st.text_input("Nombre del Acompañante", value="", key="input_acomp")
        tel_acomp = st.text_input("Teléfono Acompañante", value="", key="input_telacomp")
    with c1_5:
        nombre_resp = st.text_input("Nombre del Responsable", value="", key="input_resp")
        tel_resp = st.text_input("Teléfono Responsable", value="", key="input_telresp")

    st.markdown('</div>', unsafe_allow_html=True)

# --- TAB 2
with tab2:
    st.markdown('<div class="stCardModule">', unsafe_allow_html=True)
    st.markdown('<div><span class="badge-modulo">MÓDULO 2</span><b style="color: #0f172a; font-size: 15px;">Anamnesis y Antecedentes Médicos</b></div><br>', unsafe_allow_html=True)
    motivo = st.text_area("Motivo de Consulta (Textual del paciente)", value="", placeholder="Ej: Presenta dolor agudo en molar inferior...", key="input_motivo")
    enfermedad_actual = st.text_area("Historia de la Enfermedad Actual", value="", placeholder="Describa el inicio, frecuencia y evolución...", key="input_enfermedad")

    st.markdown('<span class="subseccion-titulo">➖ ANTECEDENTES MÉDICOS (DILIGENCIAR CADA ÍTEM)</span><br><br>', unsafe_allow_html=True)
    
    lista_antecedentes = [
        "1. Tratamiento médico", "2. Ingestión medicamentos", "3. Reacciones alérgicas (Anestesia/Antibióticos)",
        "4. Hemorragias", "5. Irradiaciones", "6. Sinusitis", "7. Enfermedad respiratoria",
        "8. Cardiopatías", "9. Diabetes", "10. Fiebre reumática", "11. Hepatitis",
        "12. Hipertensión", "13. Embarazo", "14. Enfermedades renales", "15. Enfermedades gastrointestinales",
        "16. Órganos de los sentidos", "Otros"
    ]

    antecedentes_dict = {}
    col_ant1, col_ant2 = st.columns(2)
    for i, item in enumerate(lista_antecedentes):
        with (col_ant1 if i % 2 == 0 else col_ant2):
            antecedentes_dict[item] = st.radio(
                item, 
                ["NO", "SI", "NO SABE"], 
                index=None,
                horizontal=True, 
                key=f"ant_{i}"
            )

    obs_antecedentes = st.text_area("Observaciones de Antecedentes Médicos", value="", key="input_obsant")

    st.markdown('<span class="subseccion-titulo">➖ HIGIENE ORAL Y SALUD BUCAL</span><br><br>', unsafe_allow_html=True)
    c_hig1, c_hig2, c_hig3 = st.columns(3)
    with c_hig1:
        u_visita_fecha = st.date_input("Última visita al Odontólogo", value=date.today(), key="input_uvisita")
        u_visita_motivo = st.text_input("Motivo última visita", value="", key="input_motivovisita")
        higiene_oral_est = st.radio("Higiene Oral General", ["Bueno (B)", "Regular (R)", "Malo (M)"], index=None, horizontal=True, key="input_higoral")
    with c_hig2:
        cepillo_dental = st.radio("¿Usa Cepillo Dental?", ["SI", "NO"], index=None, horizontal=True, key="input_cepillo")
        veces_al_dia = st.number_input("¿Cuántas veces al día?", min_value=0, max_value=10, value=0, key="input_veces")
    with c_hig3:
        seda_dental = st.radio("¿Usa Seda Dental?", ["SI", "NO"], index=None, horizontal=True, key="input_seda")
        enjuagues = st.radio("¿Usa Enjuagues Bucales?", ["SI", "NO"], index=None, horizontal=True, key="input_enj")

    st.markdown('</div>', unsafe_allow_html=True)

# --- TAB 3
with tab3:
    st.markdown('<div class="stCardModule">', unsafe_allow_html=True)
    st.markdown('<div><span class="badge-modulo">MÓDULO 3</span><b style="color: #0f172a; font-size: 15px;">Examen Físico Estomatológico</b></div><br>', unsafe_allow_html=True)
    
    st.markdown('<span class="subseccion-titulo">➖ TEJIDOS BLANDOS Y ESTRUCTURAS BUCALES (MARCAR SI PRESENTA ANORMALIDAD)</span><br><br>', unsafe_allow_html=True)
    elementos_estomatologicos = [
        "1. A.T.M.", "2. Labios", "3. Lengua", "4. Paladar", "5. Piso de boca",
        "6. Carrillos", "7. Glándulas salivares", "8. Maxilares", "9. Senos maxilares",
        "10. Músculos masticadores", "11. Ganglios", "12. Oclusión", "13. Frenillos",
        "14. Mucosas", "15. Encías", "16. Amígdalas"
    ]
    estomatologico_dict = {}
    col_e1, col_e2 = st.columns(2)
    for i, elem in enumerate(elementos_estomatologicos):
        with (col_e1 if i % 2 == 0 else col_e2):
            estomatologico_dict[elem] = st.checkbox(f"{elem} (Anormal)", key=f"est_{i}")

    st.markdown('<span class="subseccion-titulo">➖ HÁBITOS NOCIVOS</span><br><br>', unsafe_allow_html=True)
    habitos_lista = ["Bruxismo", "Deglución atípica", "Empuje lingual", "Fumar", "Morder objetos", "Onicofagia", "Respirador oral", "Uso palillos", "Succión digital", "Otros"]
    habitos_dict = {}
    col_h1, col_h2 = st.columns(2)
    for i, hab in enumerate(habitos_lista):
        with (col_h1 if i % 2 == 0 else col_h2):
            habitos_dict[hab] = st.checkbox(hab, key=f"hab_{i}")

    st.markdown('<span class="subseccion-titulo">➖ EXAMEN DENTAL, PERIODONTAL Y HALLAZGOS GENERALES</span><br><br>', unsafe_allow_html=True)
    col_p1, col_p2, col_p3 = st.columns(3)
    with col_p1:
        st.markdown("**Examen Dental**")
        ex_supernumerarios = st.checkbox("Supernumerarios", key="chk_sup")
        ex_abrasion = st.checkbox("Abrasión", key="chk_abr")
        ex_manchas = st.checkbox("Manchas - Cambios de color", key="chk_man")
        ex_patologia_pulpar = st.checkbox("Patología pulpar - Abscesos", key="chk_pul")
    with col_p2:
        st.markdown("**Examen Periodontal**")
        perio_bolsas = st.checkbox("Bolsas - Movilidad", key="chk_bol")
        perio_placa = st.checkbox("Placa blanda", key="chk_pla")
        perio_calculos = st.checkbox("Cálculos", key="chk_cal")
    with col_p3:
        st.markdown("**Hallazgos Generales**")
        hallaz_ortodoncia = st.checkbox("Ortodoncia", key="chk_ort")
        hallaz_protesis = st.checkbox("Prótesis", key="chk_pro")

    obs_examen_fisico = st.text_area("Observaciones del Examen Físico", value="", key="input_obsexam")

    st.markdown('<span class="subseccion-titulo">➖ HÁBITOS ALIMENTICIOS</span><br><br>', unsafe_allow_html=True)
    c_ali1, c_ali2 = st.columns(2)
    with c_ali1:
        ingesta_carbohidratos = st.radio("Ingesta de Carbohidratos (Azúcares / Harinas)", ["Baja", "Media", "Alta (5-7)"], index=None, horizontal=True, key="input_carb")
    with c_ali2:
        num_comidas = st.radio("Número de Comidas Diarias", ["< 3", "3 - 4", "> 4"], index=None, horizontal=True, key="input_com")

    st.markdown('</div>', unsafe_allow_html=True)

# --- TAB 4
with tab4:
    st.markdown('<div class="stCardModule">', unsafe_allow_html=True)
    st.markdown('<div><span class="badge-modulo">MÓDULO 4</span><b style="color: #0f172a; font-size: 16px;">Odontograma y Registro FDI</b></div><br>', unsafe_allow_html=True)
    st.markdown('<span class="subseccion-titulo">➖ ESQUEMA DENTAL Y CONVENCIONES CLÍNICAS</span><br><br>', unsafe_allow_html=True)

    tipo_dentadura = st.radio("Tipo de Dentadura Presente", ["Dentadura Permanente", "Dentadura Temporal", "Dentadura Mixta"], index=None, horizontal=True, key="input_dent")

    ruta_odontograma = None
    for posible_nombre in ["odontograma.jpg", "odontograma.jpeg", "odontograma.png", "image_318c46.jpg"]:
        if os.path.exists(posible_nombre):
            ruta_odontograma = posible_nombre
            break

    if ruta_odontograma:
        convenciones = {
            "Caries": ("rojo", "circle"),
            "Amalgama": ("azul", "dot"),
            "Resina o ionómero": ("verde", "dot"),
            "Cemento temporal": ("gris", "dot"),
            "Amalgama desadaptada": ("rojo", "ring_blue"),
            "Resina o ionómero desadaptado": ("verde", "ring_red"),
            "Endodoncia indicada": ("rojo", "triangle"),
            "Endodoncia realizada": ("azul", "triangle"),
            "Exodoncia indicada por caries": ("rojo", "x"),
            "Exodoncia indicada no por caries": ("azul", "x"),
            "Diente perdido por caries": ("rojo", "line"),
            "Diente perdido no por caries": ("azul", "line"),
            "Sellante adaptado": ("azul", "s"),
            "Sellante desadaptado": ("rojo", "s"),
            "Diente en erupción": ("azul", "up"),
            "Diente sin erupcionar": ("azul", "left"),
            "Corona adaptada": ("verde", "o"),
            "Corona desadaptada": ("rojo", "o"),
            "Prótesis adaptada": ("azul", "equals"),
            "Prótesis desadaptada": ("rojo", "equals"),
            "Incrustación": ("morado", "dot"),
        }
        colores = {
            "rojo": "#dc2626", "azul": "#2563eb", "verde": "#16a34a",
            "gris": "#64748b", "morado": "#9333ea"
        }
        simbolos_convenciones = {
            "circle": "○", "dot": "●", "ring_blue": "◉", "ring_red": "◉",
            "triangle": "▲", "x": "✕", "line": "━", "s": "S",
            "up": "↑", "left": "←", "o": "O", "equals": "=",
        }
        nombres_colores = {
            "rojo": "Rojo", "azul": "Azul", "verde": "Verde",
            "gris": "Gris", "morado": "Morado"
        }

        st.markdown("**Haz clic sobre el diente o la superficie donde va la marca:**")
        ANCHO_VISOR = 1000    
        TAMANO_MARCAS = 0.40   

        imagen_base = Image.open(ruta_odontograma).convert("RGB")
        ancho_img, alto_img = imagen_base.size
        factor = (ancho_img / ANCHO_VISOR) * TAMANO_MARCAS

        def r(valor):
            return max(1, int(round(valor * factor)))

        try:
            fuente_s = ImageFont.load_default(size=r(22))
        except TypeError:
            fuente_s = ImageFont.load_default()

        imagen_marcada = imagen_base.copy()
        lienzo = ImageDraw.Draw(imagen_marcada)

        def dibujar_marca(lienzo, marca):
            x, y = marca["x"], marca["y"]
            color_nombre, figura = convenciones[marca["convencion"]]
            color = colores[color_nombre]
            radio = r(11)
            grosor = r(4)
            if figura == "circle":
                lienzo.ellipse((x - radio, y - radio, x + radio, y + radio), outline=color, width=grosor)
            elif figura == "ring_blue":
                lienzo.ellipse((x - radio, y - radio, x + radio, y + radio), outline="#2563eb", width=grosor)
                lienzo.ellipse((x - r(5), y - r(5), x + r(5), y + r(5)), fill=color)
            elif figura == "ring_red":
                lienzo.ellipse((x - radio, y - radio, x + radio, y + radio), outline="#dc2626", width=grosor)
                lienzo.ellipse((x - r(5), y - r(5), x + r(5), y + r(5)), fill=color)
            elif figura == "dot":
                lienzo.ellipse((x - r(7), y - r(7), x + r(7), y + r(7)), fill=color)
            elif figura == "triangle":
                lienzo.polygon([(x, y - r(13)), (x - r(12), y + r(10)), (x + r(12), y + r(10))], fill=color)
            elif figura == "x":
                lienzo.line((x - r(10), y - r(10), x + r(10), y + r(10)), fill=color, width=grosor)
                lienzo.line((x + r(10), y - r(10), x - r(10), y + r(10)), fill=color, width=grosor)
            elif figura == "line":
                lienzo.line((x - r(14), y, x + r(14), y), fill=color, width=r(5))
            elif figura == "s":
                lienzo.text((x, y), "S", fill=color, font=fuente_s, anchor="mm")
            elif figura == "o":
                lienzo.ellipse((x - r(10), y - r(10), x + r(10), y + r(10)), outline=color, width=grosor)
            elif figura == "equals":
                lienzo.line((x - r(13), y - r(5), x + r(13), y - r(5)), fill=color, width=grosor)
                lienzo.line((x - r(13), y + r(5), x + r(13), y + r(5)), fill=color, width=grosor)
            elif figura == "up":
                lienzo.line((x, y + r(12), x, y - r(10)), fill=color, width=grosor)
                lienzo.line((x, y - r(10), x - r(7), y - r(2)), fill=color, width=grosor)
                lienzo.line((x, y - r(10), x + r(7), y - r(2)), fill=color, width=grosor)
            elif figura == "left":
                lienzo.line((x + r(12), y, x - r(10), y), fill=color, width=grosor)
                lienzo.line((x - r(10), y, x - r(2), y - r(7)), fill=color, width=grosor)
                lienzo.line((x - r(10), y, x - r(2), y + r(7)), fill=color, width=grosor)

        for marca in st.session_state.marcas_odontograma:
            dibujar_marca(lienzo, marca)

        clave_canvas = f"odontograma_canvas_{st.session_state.odonto_version}"
        st.markdown(
            "<style>iframe[title='streamlit_image_coordinates.streamlit_image_coordinates']"
            "{display:block;margin:0 auto;max-width:100%;}</style>",
            unsafe_allow_html=True
        )
        col_izq, col_centro, col_der = st.columns([1, 10, 1])
        with col_centro:
            st.markdown('<div style="display:flex; justify-content:center; width:100%;">', unsafe_allow_html=True)
            coordenada = streamlit_image_coordinates(
                imagen_marcada,
                width=ANCHO_VISOR,
                key=clave_canvas
            )
            st.markdown('</div>', unsafe_allow_html=True)

        if coordenada:
            firma_click = (clave_canvas, coordenada["x"], coordenada["y"], coordenada.get("unix_time"))
            if st.session_state.ultimo_click_odonto != firma_click:
                st.session_state.ultimo_click_odonto = firma_click

                # Convertir el clic (píxeles en pantalla) a píxeles de la imagen original
                ancho_mostrado = coordenada.get("width") or ANCHO_VISOR
                alto_mostrado = coordenada.get("height") or (alto_img * ANCHO_VISOR / ancho_img)
                x_real = int(coordenada["x"] * ancho_img / ancho_mostrado)
                y_real = int(coordenada["y"] * alto_img / alto_mostrado)

                convencion = st.session_state.convencion_odontograma
                nueva_marca = {
                    "x": x_real,
                    "y": y_real,
                    "convencion": convencion,
                    "Diente": f"Ubicación ({int(coordenada['x'])}, {int(coordenada['y'])})",
                    "Hallazgo": convencion,
                    "Superficies": "Pieza completa",
                    "Observación": "Marcada directamente sobre el odontograma"
                }
                st.session_state.marcas_odontograma.append(nueva_marca)
                st.session_state.plan_tratamiento.append(nueva_marca.copy())
                st.session_state.odonto_version += 1
                st.rerun()

        color_activo, figura_activa = convenciones[st.session_state.convencion_odontograma]
        simbolo_activo = simbolos_convenciones[figura_activa]
        st.info(
            f"Signo seleccionado: {simbolo_activo} **{st.session_state.convencion_odontograma}** "
            f"· Color: **{nombres_colores[color_activo]}**"
        )

        st.markdown("**Selecciona el signo que quieres marcar:**")
        botones_convenciones = st.columns(4)
        for indice, nombre in enumerate(convenciones):
            color, figura = convenciones[nombre]
            simbolo = simbolos_convenciones[figura]
            activo = "✅ " if nombre == st.session_state.convencion_odontograma else ""
            etiqueta = f"{activo}{simbolo}  {nombre}\n{nombres_colores[color]}"
            with botones_convenciones[indice % 4]:
                if st.button(etiqueta, key=f"convencion_{figura}_{nombre}", use_container_width=True):
                    st.session_state.convencion_odontograma = nombre
                    st.rerun()

        col_deshacer, col_borrar = st.columns(2)
        with col_deshacer:
            if st.button("↩️ Deshacer última marca", key="deshacer_marca_odontograma", use_container_width=True,
                        disabled=not st.session_state.marcas_odontograma):
                st.session_state.marcas_odontograma.pop()
                if st.session_state.plan_tratamiento:
                    st.session_state.plan_tratamiento.pop()
                st.session_state.odonto_version += 1
                st.rerun()
        with col_borrar:
            if st.button("🧹 Borrar todas las marcas", key="borrar_marcas_odontograma", use_container_width=True):
                st.session_state.marcas_odontograma = []
                st.session_state.plan_tratamiento = []
                st.session_state.odonto_version += 1
                st.rerun()
        st.caption(f"Marcas registradas: {len(st.session_state.marcas_odontograma)}")
    else:
        st.info("💡 Asegúrate de guardar la imagen del esquema dental en la misma carpeta como 'odontograma.jpg' o 'odontograma.png'.")

    st.write("---")

    if st.session_state.marcas_odontograma:
        st.write("---")
        st.markdown("**Tabla de ubicaciones y convenciones registradas**")
        tabla_odontograma = pd.DataFrame(st.session_state.marcas_odontograma)
        st.dataframe(
            tabla_odontograma[["Diente", "Hallazgo", "Superficies", "Observación"]].rename(columns={"Diente": "Ubicación"}),
            use_container_width=True,
            hide_index=True
        )

    st.markdown('<span class="subseccion-titulo">➖ AYUDAS DIAGNÓSTICAS Y ÍNDICES</span><br><br>', unsafe_allow_html=True)
    rx1, rx2, rx3, rx4 = st.columns(4)
    with rx1:
        rx_periapical = st.number_input("Rx Periapical (Placas)", min_value=0, value=0, key="input_rxper")
        rx_oclusal = st.number_input("Rx Oclusal (Placas)", min_value=0, value=0, key="input_rxocl")
    with rx2:
        rx_panoramica = st.number_input("Rx Panorámica", min_value=0, value=0, key="input_rxpan")
        rx_otra = st.text_input("Otra Radiografía", value="", key="input_rxotra")
    with rx3:
        placas_tomadas = st.number_input("Placas Tomadas", min_value=0, value=0, key="input_pltom")
        placas_danadas = st.number_input("Placas Dañadas", min_value=0, value=0, key="input_pldan")
    with rx4:
        pct_placa_bacteriana = st.number_input("% Placa Bacteriana", min_value=0, max_value=100, value=0, key="input_pctplaca")
        pronostico_gral = st.selectbox("Pronóstico", ["Seleccione...", "Favorable", "Desfavorable"], key="input_pron")

    st.markdown('<span class="subseccion-titulo">➖ DIAGNÓSTICOS Y PLAN GENERAL</span><br><br>', unsafe_allow_html=True)
    cd1, cd2 = st.columns(2)
    with cd1:
        diag_presuntivo = st.text_input("Diagnóstico Presuntivo", value="", key="input_diagpres")
        diag_principal = st.text_input("Diagnóstico Principal Definitivo", value="", key="input_diagprinc")
        cod_principal = st.text_input("Código CIE-10 Principal", value="", key="input_codprinc")
    with cd2:
        diag_secundario = st.text_input("Diagnóstico Secundario", value="", key="input_diagsec")
        cod_secundario = st.text_input("Código CIE-10 Secundario", value="", key="input_codsec")
        citas_programar = st.number_input("No. Citas a Programar", min_value=1, value=1, key="input_citasprog")

    st.markdown("**Áreas del Plan de Tratamiento:**")
    plan_areas = st.multiselect("Marcar Especialidades Requeridas", ["Promoción y Prevención", "Operatoria", "Endodoncia", "Cirugía", "Rehabilitación", "Otro"], default=[], key="input_planareas")
    desc_plan_tratamiento = st.text_area("Descripción Detallada del Plan de Tratamiento", value="", key="input_descplan")

    st.markdown('</div>', unsafe_allow_html=True)

# --- TAB 5
with tab5:
    st.markdown('<div class="stCardModule">', unsafe_allow_html=True)
    st.markdown('<div><span class="badge-modulo">MÓDULO 5</span><b style="color: #0f172a; font-size: 15px;">Evolución del Tratamiento</b></div><br>', unsafe_allow_html=True)
    col_ev1, col_ev2, col_ev3 = st.columns([1, 1, 2])
    with col_ev1:
        fecha_ev = st.date_input("Fecha Tratamiento", value=date.today(), key="input_fechaev")
        diente_ev = st.text_input("Diente / Sitio / Cavidad", value="", key="input_dienteev")
    with col_ev2:
        tratamiento_ejecutado = st.text_input("Tratamiento Ejecutado en Sesión", value="", key="input_tratejec")
    with col_ev3:
        st.write("")
        st.write("")
        if st.button("📝 REGISTRAR EVOLUCIÓN"):
            if tratamiento_ejecutado:
                st.session_state.evoluciones.append({
                    "Fecha y Hora": fecha_ev.strftime("%Y-%m-%d"),
                    "Diente/Sitio": diente_ev,
                    "Tratamiento Ejecutado": tratamiento_ejecutado
                })
                st.success("Evolución guardada.")

    if st.session_state.evoluciones:
        st.write("---")
        st.dataframe(pd.DataFrame(st.session_state.evoluciones), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- TAB 6
with tab6:
    st.markdown('<div class="stCardModule">', unsafe_allow_html=True)
    st.markdown('<div><span class="badge-modulo">MÓDULO 6</span><b style="color: #0f172a; font-size: 15px;">Consentimientos Informados y Firmas Digitales</b></div><br>', unsafe_allow_html=True)
    
    st.markdown('<span class="subseccion-titulo">📋 DILIGENCIAMIENTO DE CONSENTIMIENTO INFORMADO</span><br><br>', unsafe_allow_html=True)
    
    consentimientos_disponibles = [
        "Consentimiento Informado para Higiene Oral",
        "Consentimiento Informado para Aplicación de Flúor Barniz",
        "Consentimiento Informado para Raspaje Supragingival"
    ]
    consentimientos_seleccionados = st.multiselect(
        "Seleccione los consentimientos que desea diligenciar:",
        consentimientos_disponibles,
        default=[],
        key="input_tipocons"
    )

    aceptaciones_consentimiento = {}
    fecha_proxima_fluor = None
    obs_consentimiento_adicional = []
    obs_higiene = ""
    obs_fluor = ""
    obs_raspaje = ""
    reacciones_previas_fluor = ""
    instrumentos_usados = []
    zonas_raspaje = ""

    if "Consentimiento Informado para Higiene Oral" in consentimientos_seleccionados:
        st.info("ℹ️ **Procedimiento:** Eliminación de placa bacteriana, manchas y cálculos superficiales mediante el uso de instrumentos manuales y/o mecánicos con el fin de mejorar la salud bucal y prevenir enfermedades como gingivitis y periodontitis.")
        
        with st.expander("📄 Ver y Editar Datos del Consentimiento (Higiene Oral)", expanded=True):
            st.markdown(f"**Nombre y Apellido:** {nombre_paciente if nombre_paciente else '_______________'} &nbsp;&nbsp;|&nbsp;&nbsp; **Documento:** {num_doc if num_doc else '_______________'} &nbsp;&nbsp;|&nbsp;&nbsp; **Edad:** {edad} años  \n**Fecha de Atención:** {fecha_hc.strftime('%Y-%m-%d')}")
            
            obs_higiene = st.text_area(
                "Observaciones particulares / Comentarios adicionales del procedimiento:",
                value="",
                placeholder="Ej: Paciente presenta ligera sensibilidad previa en cuadrante 2...",
                key="obs_ho"
            )
            
            st.markdown("""
            **Posibles efectos secundarios o molestias explicadas:**
            * Sensibilidad dental transitoria con estímulos fríos o calientes.
            * Sangrado o irritación leve en las encías.
            * Inflamación o enrojecimiento gingival pasajero.
            * Molestias al masticar o al cepillarse durante las primeras horas posteriores a la atención.

            *El paciente declara haber recibido la información completa sobre el procedimiento, sus beneficios, riesgos y cuidados posteriores, y manifiesta estar de acuerdo con su realización.*
            """)
        
        aceptaciones_consentimiento["higiene"] = st.checkbox("El paciente y/o acudiente declara haber leído, comprendido y ACEPTA la realización de la Higiene Oral.", key="chk_acp1")
        obs_consentimiento_adicional.append(obs_higiene)

    if "Consentimiento Informado para Aplicación de Flúor Barniz" in consentimientos_seleccionados:
        st.info("ℹ️ **Procedimiento:** Aplicación preventiva de flúor barniz en superficies dentarias para retardar y detener la caries dental. Población objeto: niños, niñas y jóvenes entre 1 y 17 años (mínimo 2 veces al año, cada 6 meses).")
        
        with st.expander("📄 Ver y Editar Datos del Consentimiento (Aplicación de Flúor)", expanded=True):
            st.markdown(f"**Nombre y Apellido:** {nombre_paciente if nombre_paciente else '_______________'} &nbsp;&nbsp;|&nbsp;&nbsp; **Documento:** {num_doc if num_doc else '_______________'} &nbsp;&nbsp;|&nbsp;&nbsp; **Edad:** {edad} años  \n**Fecha de Atención:** {fecha_hc.strftime('%Y-%m-%d')}")
            
            c_fl1, c_fl2 = st.columns(2)
            with c_fl1:
                fecha_proxima_fluor = st.date_input("Fecha programada para próxima aplicación (6 meses):", value=date.today(), key="input_proxfluor")
            with c_fl2:
                reacciones_previas_fluor = st.text_input("Antecedentes de alergia/reacción a barniz:", value="", key="input_reacfluor")
            
            obs_fluor = st.text_area(
                "Notas o recomendaciones específicas adicionadas:",
                value="",
                placeholder="Ej: Aplicación focalizada en molares superiores...",
                key="obs_fl"
            )

            st.markdown("""
            **Información Importante:**
            - El secado rápido del barniz libera de forma lenta y continua iones de fluoruro cubriendo el esmalte dental para reducir la desmineralización.
            - **Cambio de color:** Puede presentarse un leve cambio temporal en el color del diente debido al tono del barniz.
            - **Cuidados posteriores (Durante las primeras 4 horas):** Evitar alimentos duros o pegajosos, productos con alcohol, enjuagues o bebidas calientes. Preferiblemente realizar el cepillado dental hasta la mañana siguiente.
            """)
        
        aceptaciones_consentimiento["fluor"] = st.checkbox("El paciente y/o acudiente declara haber sido informado de los riesgos/cuidados y ACEPTA la aplicación de flúor barniz.", key="chk_acp2")
        obs_consentimiento_adicional.append(obs_fluor)

    if "Consentimiento Informado para Raspaje Supragingival" in consentimientos_seleccionados:
        st.info("ℹ️ **Procedimiento:** Eliminación mecánica de depósitos calcificados de placa bacteriana (cálculos/sarro) mediante instrumentos manuales, sónicos o ultrasónicos (frecuencia sugerida: 1 a 2 veces por año).")
        
        with st.expander("📄 Ver y Editar Datos del Consentimiento (Raspaje Supragingival)", expanded=True):
            st.markdown(f"**Nombre y Apellido:** {nombre_paciente if nombre_paciente else '_______________'} &nbsp;&nbsp;|&nbsp;&nbsp; **Documento:** {num_doc if num_doc else '_______________'}  \n**Fecha de Atención:** {fecha_hc.strftime('%Y-%m-%d')}")
            
            col_ras1, col_ras2 = st.columns(2)
            with col_ras1:
                instrumentos_usados = st.multiselect("Instrumental a emplear:", ["Instrumentos Manuales", "Instrumentos Sónicos", "Instrumentos Ultrasónicos"], default=[], key="input_inst")
            with col_ras2:
                zonas_raspaje = st.text_input("Sectores / Cuadrantes a tratar:", value="", key="input_zonasrasp")
            
            obs_raspaje = st.text_area(
                "Observaciones o hallazgos adicionales antes del procedimiento:",
                value="",
                placeholder="Ej: Se evidencia sangrado gingival en sector anterior...",
                key="obs_rs"
            )

            st.markdown("""
            **1. Objetivos y Beneficios:** Prevenir enfermedades periodontal/gingivitis, disminuir la halitosis y mejorar la salud bucal.  
            **2. Riesgos Informados:** Sensibilidad dental temporal al frío/calor, pequeños sangrados, molestias leves o irritación gingival pasajera.  
            **3. Riesgos de no realizarlo:** Acumulación de sarro, riesgo de gingivitis, periodontitis, movilidad y pérdida de piezas dentales.  

            *Autorizo de manera libre y voluntaria la realización del procedimiento de raspaje supragingival.*
            """)
        
        aceptaciones_consentimiento["raspaje"] = st.checkbox("El paciente declara haber comprendido la información y AUTORIZA de manera libre y voluntaria el Raspaje Supragingival.", key="chk_acp3")
        obs_consentimiento_adicional.append(obs_raspaje)

    tipo_consentimiento = ", ".join(consentimientos_seleccionados) if consentimientos_seleccionados else "Ninguno / No aplica para esta consulta"
    acepta_consentimiento = all(aceptaciones_consentimiento.values()) if aceptaciones_consentimiento else False
    obs_consentimiento_adicional = " | ".join(obs_consentimiento_adicional)

    st.write("---")

    # CARGA DE FIRMAS DIGITALES
    st.markdown('<span class="subseccion-titulo">✍️ CARGA DE FIRMAS DIGITALES</span><br><br>', unsafe_allow_html=True)
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        st.markdown("**Firma del Paciente / Acompañante**")
        file_firma_paciente = st.file_uploader("Adjuntar firma del paciente (PNG, JPG, PDF)", type=["png", "jpg", "jpeg", "pdf"], key="file_pac")
        if file_firma_paciente and file_firma_paciente.type != "application/pdf":
            st.image(file_firma_paciente, width=160)

    with col_f2:
        st.markdown("**Firma del Higienista / Estudiante / Odontólogo**")
        nombre_odonto = st.text_input("Nombre del Profesional / Estudiante", value="", key="input_nomodo")
        tarjeta_prof = st.text_input("Registro / Código Profesional", value="", key="input_regprof")
        file_firma_odonto = st.file_uploader("Adjuntar firma del profesional (PNG, JPG, PDF)", type=["png", "jpg", "jpeg", "pdf"], key="file_odo")
        if file_firma_odonto and file_firma_odonto.type != "application/pdf":
            st.image(file_firma_odonto, width=160)

    st.write("---")
    if st.button("🔒 GENERAR Y COMPILAR PDF COMPLETO", use_container_width=True):
        if nombre_paciente and nombre_odonto:
            datos_hc = {
                "Fecha de Atención": fecha_hc.strftime("%Y-%m-%d"),
                "Historia Clínica N°": hc_num,
                "EPS": eps,
                "Tipo Plan": tipo_plan if tipo_plan != "Seleccione..." else "NO ESPECIFICADO",
                "Condición Usuario": condicion_usuario if condicion_usuario != "Seleccione..." else "NO ESPECIFICADO",
                "Paciente": nombre_paciente,
                "Tipo Doc": tipo_doc if tipo_doc != "Seleccione..." else "CC",
                "Documento Paciente": num_doc,
                "Sexo": sexo if sexo else "NO ESPECIFICADO",
                "Edad": edad,
                "Estado Civil": estado_civil if estado_civil != "Seleccione..." else "NO ESPECIFICADO",
                "Ocupación": ocupacion,
                "Fecha Nacimiento": fecha_nac.strftime("%Y-%m-%d"),
                "Teléfono": telefono,
                "Dirección": direccion,
                "Ciudad/Departamento": ciudad_depto,
                "Acompañante": f"{nombre_acomp} (Tel: {tel_acomp})" if nombre_acomp else "Ninguno",
                "Responsable": f"{nombre_resp} (Tel: {tel_resp})" if nombre_resp else "Ninguno",
                "Motivo de Consulta": motivo,
                "Enfermedad Actual": enfermedad_actual,
                "Antecedentes": antecedentes_dict,
                "Obs Antecedentes": obs_antecedentes,
                "Higiene Oral": f"Visita: {u_visita_fecha} | Motivo: {u_visita_motivo} | Estado: {higiene_oral_est} | Cepillo: {cepillo_dental} ({veces_al_dia}/día) | Seda: {seda_dental} | Enjuague: {enjuagues}",
                "Estomatologico": estomatologico_dict,
                "Habitos": habitos_dict,
                "Dental": f"Supernumerarios: {'SI' if ex_supernumerarios else 'NO'}, Abrasión: {'SI' if ex_abrasion else 'NO'}, Manchas: {'SI' if ex_manchas else 'NO'}, Pat. Pulpar: {'SI' if ex_patologia_pulpar else 'NO'}",
                "Periodontal": f"Bolsas: {'SI' if perio_bolsas else 'NO'}, Placa: {'SI' if perio_placa else 'NO'}, Cálculos: {'SI' if perio_calculos else 'NO'}",
                "Hallazgos Gen": f"Ortodoncia: {'SI' if hallaz_ortodoncia else 'NO'}, Prótesis: {'SI' if hallaz_protesis else 'NO'}",
                "Obs Examen Fisico": obs_examen_fisico,
                "Alimenticios": f"Carbohidratos: {ingesta_carbohidratos} | Comidas/día: {num_comidas}",
                "Dentadura": tipo_dentadura if tipo_dentadura else "No especificada",
                "Radiografias": f"Periapical: {rx_periapical}, Oclusal: {rx_oclusal}, Panorámica: {rx_panoramica}, Otra: {rx_otra} | Tomadas: {placas_tomadas}, Dañadas: {placas_danadas}",
                "Indices": f"Placa Bacteriana: {pct_placa_bacteriana}% | Pronóstico: {pronostico_gral}",
                "Diags": f"Presuntivo: {diag_presuntivo} | Principal: {diag_principal} ({cod_principal}) | Secundario: {diag_secundario} ({cod_secundario})",
                "Plan Resumen": f"Áreas: {', '.join(plan_areas)} | Citas: {citas_programar} | Detalle: {desc_plan_tratamiento}",
                "Consentimiento Tipo": tipo_consentimiento,
                "Consentimientos Seleccionados": tipo_consentimiento,
                "Consentimiento Aceptado": "SÍ" if acepta_consentimiento else "NO / NO APLICA",
                "Proxima Cita Fluor": fecha_proxima_fluor.strftime("%Y-%m-%d") if fecha_proxima_fluor else "N/A",
                "Obs Higiene Oral": obs_higiene,
                "Obs Fluor": obs_fluor,
                "Obs Raspaje": obs_raspaje,
                "Obs Consentimiento Adicional": obs_consentimiento_adicional,
                "Reacciones Previas Fluor": reacciones_previas_fluor,
                "Instrumentos Raspaje": ", ".join(instrumentos_usados) if instrumentos_usados else "N/A",
                "Zonas Raspaje": zonas_raspaje,
                "Odontólogo Tratante": nombre_odonto,
                "Código/Registro": tarjeta_prof
            }

            pdf_data = generar_pdf_hc(
                datos_hc, 
                st.session_state.plan_tratamiento, 
                st.session_state.evoluciones,
                firma_paciente_file=file_firma_paciente,
                firma_odonto_file=file_firma_odonto
            )

            st.download_button(
                label="📕 DESCARGAR PDF COMPLETO CON HISTORIA Y CONSENTIMIENTO",
                data=pdf_data,
                file_name="Historia_Clinica_San_Pedro_Claver.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        else:
            st.error("⚠️ Por favor ingresa el nombre del paciente (Módulo 1) y el del profesional (Módulo 6) antes de generar el reporte PDF.")
    
    st.markdown('</div>', unsafe_allow_html=True)