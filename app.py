import streamlit as st
import pandas as pd
from datetime import datetime, date
import os
import base64
import html
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageColor, ImageFilter
from streamlit_image_coordinates import streamlit_image_coordinates
from pdf_generator import generar_pdf_hc
import odontograma as odo

st.set_page_config(
    page_title="Historia Clínica Odontológica - San Pedro Claver",
    page_icon="🦷",
    layout="wide"
)

# Ocultar el menú de hamburguesa y barra superior de Streamlit
hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
[data-testid="stHeader"] {visibility: hidden;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# Cargar CSS
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

def _html(fragmento: str) -> str:
    # Streamlit interpreta como Markdown las líneas con sangría: se envía en una sola línea.
    return " ".join(linea.strip() for linea in fragmento.splitlines() if linea.strip())


def encabezado(logo_base64: str, institucion: str) -> None:
    logo = ""
    if logo_base64:
        logo = (
            '<div class="tw:shrink-0 tw:rounded-2xl tw:bg-white tw:p-3 tw:shadow-lg tw:ring-4 tw:ring-white/30 '
            'tw:transition tw:duration-300 tw:hover:scale-105 tw:hover:-rotate-2">'
            f'<img src="data:image/png;base64,{logo_base64}" alt="Escuela de Salud San Pedro Claver" '
            'class="tw:h-16 tw:w-40 tw:object-contain"></div>'
        )
    st.markdown(_html(f"""
    <div class="tw:group tw:relative tw:mb-4 tw:overflow-hidden tw:rounded-3xl tw:bg-linear-to-r
                   tw:from-teal-800 tw:via-teal-700 tw:to-emerald-500 tw:px-8 tw:py-6 tw:shadow-xl
                   tw:transition tw:duration-500 tw:hover:shadow-2xl">
      <div class="tw:pointer-events-none tw:absolute tw:-right-16 tw:-top-20 tw:size-64 tw:rounded-full
                  tw:bg-white/10 tw:transition tw:duration-700 tw:group-hover:scale-125"></div>
      <div class="tw:pointer-events-none tw:absolute tw:-bottom-24 tw:right-1/3 tw:size-56 tw:rounded-full
                  tw:bg-emerald-300/10 tw:transition tw:duration-700 tw:group-hover:-translate-y-4"></div>
      <div class="tw:relative tw:flex tw:flex-col tw:items-center tw:gap-5 tw:text-center
                  tw:md:flex-row tw:md:text-left">
        {logo}
        <div class="tw:flex-1">
          <div class="tw:m-0 tw:text-xs tw:font-semibold tw:uppercase tw:tracking-[0.25em] tw:text-emerald-100">
            Simulador académico</div>
          <div class="tw:m-0 tw:text-3xl tw:font-extrabold tw:leading-tight tw:tracking-tight tw:text-white">
            Historia Clínica Odontológica</div>
          <div class="tw:m-0 tw:mt-1 tw:text-sm tw:font-medium tw:text-white/90">
            {html.escape(institucion)} — Programa de Salud Oral · Sede Neiva</div>
        </div>
        <div class="tw:flex tw:flex-col tw:items-center tw:gap-2 tw:md:items-end">
          <span class="tw:inline-flex tw:items-center tw:gap-2 tw:rounded-full tw:bg-white/20 tw:px-4 tw:py-2
                       tw:text-xs tw:font-bold tw:uppercase tw:tracking-wider tw:text-white tw:backdrop-blur
                       tw:transition tw:hover:bg-white/30">
            <span class="tw:relative tw:flex tw:size-2.5">
              <span class="tw:absolute tw:inline-flex tw:size-full tw:animate-ping tw:rounded-full tw:bg-emerald-300 tw:opacity-75"></span>
              <span class="tw:relative tw:inline-flex tw:size-2.5 tw:rounded-full tw:bg-emerald-300"></span>
            </span>
            Sesión abierta
          </span>
          <span class="tw:text-xs tw:text-white/80">🔒 Diligenciamiento seguro</span>
        </div>
      </div>
    </div>
    """), unsafe_allow_html=True)


def seccion(titulo: str, icono: str = "", modulo: int | None = None) -> None:
    """Tarjeta de título para cada sección del formulario."""
    badge = ""
    if modulo is not None:
        badge = (f'<span class="tw:rounded-full tw:bg-teal-600 tw:px-2.5 tw:py-0.5 tw:text-[0.68rem] '
                 f'tw:font-bold tw:tracking-wider tw:text-white">MÓDULO {modulo}</span>')
    st.markdown(_html(f"""
    <div class="tw:group tw:mt-6 tw:mb-3 tw:flex tw:items-center tw:gap-3 tw:rounded-2xl tw:border
                tw:border-sky-100 tw:border-l-4 tw:border-l-teal-600 tw:bg-white tw:px-5 tw:py-3
                tw:shadow-sm tw:transition tw:duration-300 tw:hover:-translate-y-0.5 tw:hover:border-teal-200
                tw:hover:shadow-md">
      <span class="tw:grid tw:size-9 tw:place-items-center tw:rounded-xl tw:bg-teal-50 tw:text-lg
                   tw:transition tw:duration-300 tw:group-hover:scale-110 tw:group-hover:bg-teal-100">{icono}</span>
      {badge}
      <span class="tw:text-sm tw:font-extrabold tw:uppercase tw:tracking-wide tw:text-teal-700">
        {html.escape(titulo)}</span>
    </div>
    """), unsafe_allow_html=True)


# El botón de descarga puede crear el PDF en el mismo clic (Streamlit 1.50 o más reciente)
DESCARGA_DIFERIDA = "deferred" in (st.download_button.__doc__ or "").lower()


def tarjeta_requisitos(requisitos, listo):
    """Lista de verificación antes de generar el PDF."""
    filas = []
    for nombre, modulo, ok, obligatorio in requisitos:
        if ok:
            icono = ('<span class="tw:grid tw:size-6 tw:shrink-0 tw:place-items-center tw:rounded-full tw:bg-emerald-500 '
                     'tw:text-xs tw:font-bold tw:text-white">✓</span>')
        elif obligatorio:
            icono = ('<span class="tw:grid tw:size-6 tw:shrink-0 tw:place-items-center tw:rounded-full tw:bg-rose-100 '
                     'tw:text-xs tw:font-bold tw:text-rose-600">!</span>')
        else:
            icono = ('<span class="tw:grid tw:size-6 tw:shrink-0 tw:place-items-center tw:rounded-full tw:bg-slate-100 '
                     'tw:text-xs tw:font-bold tw:text-slate-400">○</span>')
        etiqueta = ('<span class="tw:rounded-full tw:bg-rose-50 tw:px-2 tw:py-0.5 tw:text-[0.62rem] tw:font-bold '
                    'tw:text-rose-600">Obligatorio</span>' if obligatorio and not ok else
                    '<span class="tw:text-[0.62rem] tw:font-semibold tw:text-slate-400">Recomendado</span>'
                    if not ok else '')
        filas.append(f"""
        <div class="tw:flex tw:items-center tw:gap-3 tw:rounded-xl tw:border tw:border-slate-100 tw:bg-white tw:px-3 tw:py-2
                    tw:transition tw:duration-200 tw:hover:border-teal-200 tw:hover:bg-teal-50/40">
          {icono}
          <div class="tw:flex-1">
            <div class="tw:text-sm tw:font-semibold tw:text-slate-700">{html.escape(nombre)}</div>
            <div class="tw:text-[0.68rem] tw:text-slate-400">{modulo}</div>
          </div>
          {etiqueta}
        </div>""")
    if listo:
        titulo = "✅ Todo listo: haz clic en el botón y el PDF se descarga de una vez"
        color = "tw:border-emerald-200 tw:bg-emerald-50/60 tw:text-emerald-800"
    else:
        titulo = "⚠️ Completa los datos obligatorios para habilitar el PDF"
        color = "tw:border-rose-200 tw:bg-rose-50/60 tw:text-rose-700"
    st.markdown(_html(f"""
    <div class="tw:mt-2 tw:mb-4 tw:rounded-2xl tw:border tw:p-4 {color}">
      <div class="tw:mb-3 tw:text-sm tw:font-bold">{titulo}</div>
      <div class="tw:grid tw:gap-2 tw:md:grid-cols-2 tw:xl:grid-cols-3">{''.join(filas)}</div>
    </div>
    """), unsafe_allow_html=True)


ICONOS_MODULO = ["🗂️", "🗣️", "🔎", "🦷", "📈", "✍️"]
MODULOS = [
    "1. Datos Administrativos",
    "2. Anamnesis y Antecedentes",
    "3. Examen Estomatológico",
    "4. Odontograma y Diag.",
    "5. Evolución",
    "6. Firmas y Consentimientos",
]
NAV_KEY = "nav_modulos"  # Pestaña abierta; se cambia haciendo clic en las tarjetas del panel


def ir_a_modulo(etiqueta):
    st.session_state[NAV_KEY] = etiqueta


def panel_avance(contenedor, modulos, listo_pdf):
    """Panel de avance: anillo con el total y una tarjeta por módulo. Cada tarjeta abre su módulo."""
    total = round(100 * sum(p for _, p in modulos) / max(len(modulos), 1))
    completos = sum(1 for _, p in modulos if p >= 1)
    if listo_pdf:
        estado = ('<span class="tw:inline-flex tw:items-center tw:gap-1.5 tw:rounded-full tw:bg-emerald-100 tw:px-3 '
                  'tw:py-1.5 tw:text-xs tw:font-bold tw:text-emerald-700">✅ Lista para generar el PDF</span>')
    else:
        estado = ('<span class="tw:inline-flex tw:items-center tw:gap-1.5 tw:rounded-full tw:bg-amber-100 tw:px-3 '
                  'tw:py-1.5 tw:text-xs tw:font-bold tw:text-amber-700">✏️ En diligenciamiento</span>')
    activo = st.session_state.get(NAV_KEY, MODULOS[0])

    with contenedor.container(key="panel_avance"):
        st.markdown(_html(f"""
        <div class="tw:flex tw:flex-wrap tw:items-center tw:gap-4">
          <div class="tw:grid tw:size-16 tw:shrink-0 tw:place-items-center tw:rounded-full"
               style="background:conic-gradient(#0d9488 {total * 3.6}deg, #e2e8f0 0deg)">
            <div class="tw:grid tw:size-12 tw:place-items-center tw:rounded-full tw:bg-white tw:text-sm
                        tw:font-extrabold tw:text-teal-700">{total}%</div>
          </div>
          <div class="tw:min-w-48 tw:flex-1">
            <div class="tw:text-base tw:font-bold tw:text-slate-800">Avance de la historia clínica</div>
            <div class="tw:text-xs tw:text-slate-500">{completos} de {len(modulos)} módulos completos ·
              haz clic en un módulo para abrirlo</div>
          </div>
          {estado}
        </div>
        """), unsafe_allow_html=True)

        columnas = st.columns(len(modulos))
        for i, ((nombre, p), col) in enumerate(zip(modulos, columnas), start=1):
            pct = round(100 * p)
            if pct >= 100:
                linea, fondo_icono, relleno = "tw:bg-emerald-400", "tw:bg-emerald-50", "tw:bg-emerald-500"
                chip = ('<span class="tw:grid tw:size-6 tw:place-items-center tw:rounded-full tw:bg-emerald-500 '
                        'tw:text-xs tw:font-bold tw:text-white">✓</span>')
            elif pct > 0:
                linea, fondo_icono, relleno = "tw:bg-amber-400", "tw:bg-amber-50", "tw:bg-amber-400"
                chip = ('<span class="tw:rounded-full tw:bg-amber-100 tw:px-2 tw:py-0.5 tw:text-[0.65rem] '
                        f'tw:font-bold tw:text-amber-700">{pct}%</span>')
            else:
                linea, fondo_icono, relleno = "tw:bg-slate-200", "tw:bg-slate-100", "tw:bg-slate-300"
                chip = '<span class="tw:text-[0.65rem] tw:font-semibold tw:text-slate-400">Pendiente</span>'
            clase_activa = " tarjeta-activa" if MODULOS[i - 1] == activo else ""
            with col.container(key=f"tarjeta_{i}"):
                st.markdown(_html(f"""
                <div class="tarjeta-modulo{clase_activa} tw:relative tw:overflow-hidden tw:rounded-2xl tw:border
                            tw:border-slate-200 tw:bg-white tw:p-3.5 tw:shadow-sm">
                  <div class="tw:absolute tw:inset-x-0 tw:top-0 tw:h-1 {linea}"></div>
                  <div class="tw:flex tw:items-center tw:justify-between">
                    <span class="tarjeta-icono tw:grid tw:size-10 tw:place-items-center tw:rounded-xl tw:text-xl
                                 {fondo_icono}">{ICONOS_MODULO[i - 1]}</span>
                    {chip}
                  </div>
                  <div class="tw:mt-2 tw:text-[0.62rem] tw:font-bold tw:uppercase tw:tracking-widest tw:text-slate-400">Módulo {i}</div>
                  <div class="tw:min-h-9 tw:text-sm tw:font-bold tw:leading-tight tw:text-slate-800">{html.escape(nombre)}</div>
                  <div class="tw:mt-2 tw:h-1.5 tw:overflow-hidden tw:rounded-full tw:bg-slate-100">
                    <div class="tw:h-full tw:rounded-full tw:transition-all tw:duration-700 {relleno}" style="width:{pct}%"></div>
                  </div>
                </div>
                """), unsafe_allow_html=True)
                # Botón invisible que cubre toda la tarjeta (ver stilo.css)
                st.button(f"Abrir {nombre}", key=f"nav_{i}", on_click=ir_a_modulo, args=(MODULOS[i - 1],))


logo_b64 = get_image_base64("logo.png")
encabezado(logo_b64, "ESCUELA DE SALUD SAN PEDRO CLAVER")
panel_progreso = st.empty()  # Se llena al final, cuando ya se conocen todos los datos

# Inicializar estados de sesión
if "evoluciones" not in st.session_state:
    st.session_state.evoluciones = []

if "plan_tratamiento" not in st.session_state:
    st.session_state.plan_tratamiento = []

# Odontograma: {"17-arriba": "Caries"} por superficie y {"17": "Endodoncia indicada"} por diente
if "odo_superficies" not in st.session_state:
    st.session_state.odo_superficies = {}
if "odo_dientes" not in st.session_state:
    st.session_state.odo_dientes = {}
if "odo_historial" not in st.session_state:
    st.session_state.odo_historial = []

if "convencion_odontograma" not in st.session_state:
    st.session_state.convencion_odontograma = "Caries"

# Contador que renueva el lienzo del odontograma después de cada cambio
if "odonto_version" not in st.session_state:
    st.session_state.odonto_version = 0

# Último clic ya procesado (evita marcas duplicadas al pulsar botones)
if "ultimo_click_odonto" not in st.session_state:
    st.session_state.ultimo_click_odonto = None

# --- PESTAÑAS ---
# Todas las pestañas se siguen ejecutando (así el PDF tiene todos los datos);
# la pestaña visible la eligen las tarjetas del panel de avance.
try:
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(MODULOS, key=NAV_KEY, on_change="rerun")
    NAVEGACION_CON_TARJETAS = True
except TypeError:  # Versión de Streamlit sin esta opción: se dejan las pestañas visibles
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(MODULOS)
    NAVEGACION_CON_TARJETAS = False
if NAVEGACION_CON_TARJETAS:  # Se oculta la barra de pestañas: se navega con las tarjetas
    st.markdown("""<style>
        .stTabs [role="tablist"], .stTabs [data-testid="stTab"],
        [data-testid="stTabsScrollLeft"], [data-testid="stTabsScrollRight"],
        .stTabs [data-baseweb="tab-list"], .stTabs [data-baseweb="tab-border"],
        .stTabs [data-baseweb="tab-highlight"] { display: none !important; }
    </style>""", unsafe_allow_html=True)

# --- TAB 1: DATOS ADMINISTRATIVOS Y DE IDENTIFICACIÓN ---
with tab1:
    seccion("Datos Administrativos de la Consulta", "🗂️", modulo=0)
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

    seccion("Datos Personales del Paciente", "👤", modulo=1)
    seccion("IDENTIFICACIÓN E INFORMACIÓN GENERAL", "🪪")

    c1_1, c1_2, c1_3 = st.columns(3)
    with c1_1:
        nombre_paciente = st.text_input("Nombre del Paciente (Completo)", value="", placeholder="Nombre completo...", key="input_nombre")
        tipo_doc = st.selectbox("Tipo de Documento", ["Seleccione...", "CC", "TI", "RC", "MS", "CE", "PA", "ASI"], key="input_tipodoc")
        sexo = st.radio("Sexo", ["Hombre", "Mujer"], index=None, horizontal=True, key="input_sexo")
        tipo_plan = st.selectbox("Tipo de Plan", ["Seleccione...", "POS", "POS SUBS.", "PREPAGO", "OTRO"], key="input_tipplan")

    with c1_2:
        num_doc = st.text_input("N° de Documento", value="", placeholder="Número de documento...", key="input_numdoc")
        fecha_nac = st.date_input(
            "Fecha de Nacimiento (DD/MM/AAAA)", 
            value=date(2000, 1, 1),
            min_value=date(1920, 1, 1),
            max_value=date.today(),
            format="DD/MM/YYYY",
            key="input_fechanac"
        )
        _hoy = date.today()
        edad = _hoy.year - fecha_nac.year - ((_hoy.month, _hoy.day) < (fecha_nac.month, fecha_nac.day))
        st.session_state["input_edad_calc"] = f"{edad} años"
        st.text_input("Edad (calculada)", key="input_edad_calc", disabled=True)
        condicion_usuario = st.selectbox("Condición del Usuario", ["Seleccione...", "COTIZANTE", "BENEFICIARIO", "PENSIONADO", "OTRO"], key="input_condicion")

    with c1_3:
        direccion = st.text_input("Dirección de Vivienda", value="", placeholder="Dirección...", key="input_dir")
        telefono = st.text_input("Teléfono de Contacto", value="", placeholder="Teléfono...", key="input_tel")
        
        # Selector de Ciudad / Departamento principal de Colombia
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

    seccion("ACOMPAÑANTE Y RESPONSABLE", "👥")
    c1_4, c1_5 = st.columns(2)
    with c1_4:
        nombre_acomp = st.text_input("Nombre del Acompañante", value="", key="input_acomp")
        tel_acomp = st.text_input("Teléfono Acompañante", value="", key="input_telacomp")
    with c1_5:
        nombre_resp = st.text_input("Nombre del Responsable", value="", key="input_resp")
        tel_resp = st.text_input("Teléfono Responsable", value="", key="input_telresp")


# --- TAB 2: ANAMNESIS Y ANTECEDENTES MÉDICOS ---
with tab2:
    seccion("Anamnesis y Antecedentes Médicos", "🗣️", modulo=2)
    motivo = st.text_area("Motivo de Consulta (Textual del paciente)", value="", placeholder="Ej: Presenta dolor agudo en molar inferior...", key="input_motivo")
    enfermedad_actual = st.text_area("Historia de la Enfermedad Actual", value="", placeholder="Describa el inicio, frecuencia y evolución...", key="input_enfermedad")

    seccion("ANTECEDENTES MÉDICOS (DILIGENCIAR CADA ÍTEM)", "📋")
    
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

    seccion("HIGIENE ORAL Y SALUD BUCAL", "🪥")
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


# --- TAB 3: EXAMEN FÍSICO ESTOMATOLÓGICO ---
with tab3:
    seccion("Examen Físico Estomatológico", "🔎", modulo=3)
    
    seccion("TEJIDOS BLANDOS Y ESTRUCTURAS BUCALES (MARCAR SI PRESENTA ANORMALIDAD)", "👄")
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

    seccion("HÁBITOS NOCIVOS", "🚭")
    habitos_lista = ["Bruxismo", "Deglución atípica", "Empuje lingual", "Fumar", "Morder objetos", "Onicofagia", "Respirador oral", "Uso palillos", "Succión digital", "Otros"]
    habitos_dict = {}
    col_h1, col_h2 = st.columns(2)
    for i, hab in enumerate(habitos_lista):
        with (col_h1 if i % 2 == 0 else col_h2):
            habitos_dict[hab] = st.checkbox(hab, key=f"hab_{i}")

    seccion("EXAMEN DENTAL, PERIODONTAL Y HALLAZGOS GENERALES", "🦷")
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

    seccion("HÁBITOS ALIMENTICIOS", "🍎")
    c_ali1, c_ali2 = st.columns(2)
    with c_ali1:
        ingesta_carbohidratos = st.radio("Ingesta de Carbohidratos (Azúcares / Harinas)", ["Baja", "Media", "Alta (5-7)"], index=None, horizontal=True, key="input_carb")
    with c_ali2:
        num_comidas = st.radio("Número de Comidas Diarias", ["< 3", "3 - 4", "> 4"], index=None, horizontal=True, key="input_com")


# --- TAB 4: ODONTOGRAMA, RADIOGRAFÍAS Y DIAGNÓSTICOS ---
with tab4:
    seccion("Odontograma y Registro FDI", "🦷", modulo=4)
    seccion("ESQUEMA DENTAL Y CONVENCIONES CLÍNICAS", "🗺️")

    # ---------------- ODONTOGRAMA DIBUJADO (sistema FDI) ----------------
    denticion = st.radio("Tipo de dentición", ["Permanente", "Temporal", "Mixta"],
                         horizontal=True, key="input_dent")
    tipo_dentadura = f"Dentición {denticion}"

    # 1) Barra de convenciones: un ícono por signo (al pasar el mouse sale el nombre)
    nombres_conv = list(odo.CONVENCIONES.keys())
    por_fila = 12
    for inicio in range(0, len(nombres_conv), por_fila):
        columnas = st.columns(por_fila)
        for col, nombre in zip(columnas, nombres_conv[inicio:inicio + por_fila]):
            with col:
                tipo_btn = "primary" if nombre == st.session_state.convencion_odontograma else "secondary"
                if st.button(odo.CONVENCIONES[nombre]["icono"], key=f"conv_{nombre}", help=nombre,
                             type=tipo_btn, use_container_width=True):
                    st.session_state.convencion_odontograma = nombre
                    st.rerun()

    conv_activa = st.session_state.convencion_odontograma
    info_activa = odo.CONVENCIONES[conv_activa]
    como = {"superficie": "toca la superficie del diente",
            "diente": "toca cualquier parte del diente (se marca completo)",
            "borrar": "toca una superficie o diente para limpiarlo"}[info_activa["tipo"]]
    st.markdown(f"{info_activa['icono']} **{conv_activa}** — {como}")

    # 2) Dibujo del odontograma y detección del clic
    imagen_odo = odo.dibujar(denticion, st.session_state.odo_superficies, st.session_state.odo_dientes)
    clave_canvas = f"odontograma_canvas_{st.session_state.odonto_version}"
    # Centrar el odontograma en la página
    st.markdown(f"""<style>
        div[data-testid="stElementContainer"]:has(iframe[title="streamlit_image_coordinates.streamlit_image_coordinates"]),
        div.element-container:has(iframe[title="streamlit_image_coordinates.streamlit_image_coordinates"]) {{
            display: flex; justify-content: center; width: 100% !important;
        }}
        iframe[title="streamlit_image_coordinates.streamlit_image_coordinates"] {{
            width: {odo.ANCHO}px !important; max-width: 100%; margin: 0 auto; display: block;
        }}
    </style>""", unsafe_allow_html=True)
    coordenada = streamlit_image_coordinates(imagen_odo, width=odo.ANCHO, key=clave_canvas)

    if coordenada:
        firma_click = (clave_canvas, coordenada["x"], coordenada["y"], coordenada.get("unix_time"))
        if st.session_state.ultimo_click_odonto != firma_click:
            st.session_state.ultimo_click_odonto = firma_click
            # Pasar el clic a la escala del dibujo por si el navegador achicó la imagen
            ancho_mostrado = coordenada.get("width") or odo.ANCHO
            x = coordenada["x"] * odo.ANCHO / ancho_mostrado
            y = coordenada["y"] * odo.ANCHO / ancho_mostrado
            diente, sup = odo.detectar(denticion, x, y)
            if diente is not None:
                # Guardar copia para poder deshacer
                st.session_state.odo_historial.append(
                    (dict(st.session_state.odo_superficies), dict(st.session_state.odo_dientes)))
                clave_sup, clave_diente = f"{diente}-{sup}", str(diente)
                if info_activa["tipo"] == "superficie":
                    if st.session_state.odo_superficies.get(clave_sup) == conv_activa:
                        st.session_state.odo_superficies.pop(clave_sup)   # tocar de nuevo = quitar
                    else:
                        st.session_state.odo_superficies[clave_sup] = conv_activa
                elif info_activa["tipo"] == "diente":
                    if st.session_state.odo_dientes.get(clave_diente) == conv_activa:
                        st.session_state.odo_dientes.pop(clave_diente)
                    else:
                        st.session_state.odo_dientes[clave_diente] = conv_activa
                else:  # borrar
                    if clave_diente in st.session_state.odo_dientes:
                        st.session_state.odo_dientes.pop(clave_diente)
                    else:
                        st.session_state.odo_superficies.pop(clave_sup, None)
                st.session_state.odonto_version += 1
                st.rerun()

    # 3) Deshacer / borrar todo
    col_deshacer, col_borrar = st.columns(2)
    with col_deshacer:
        if st.button("↩️ Deshacer última marca", key="deshacer_marca_odontograma", use_container_width=True,
                     disabled=not st.session_state.odo_historial):
            st.session_state.odo_superficies, st.session_state.odo_dientes = st.session_state.odo_historial.pop()
            st.session_state.odonto_version += 1
            st.rerun()
    with col_borrar:
        if st.button("🧹 Borrar todo el odontograma", key="borrar_marcas_odontograma", use_container_width=True):
            st.session_state.odo_historial.append(
                (dict(st.session_state.odo_superficies), dict(st.session_state.odo_dientes)))
            st.session_state.odo_superficies, st.session_state.odo_dientes = {}, {}
            st.session_state.odonto_version += 1
            st.rerun()

    # 4) Índice O'Leary automático
    total_sup, sup_tenidas, pct_placa_bacteriana = odo.indice_oleary(
        denticion, st.session_state.odo_superficies, st.session_state.odo_dientes)
    st.markdown("**Índice de placa O'Leary** (se marca con el ícono amarillo de placa bacteriana)")
    o1, o2, o3 = st.columns(3)
    o1.metric("Total superficies", total_sup)
    o2.metric("Superficies teñidas", sup_tenidas)
    o3.metric("Índice O'Leary", f"{pct_placa_bacteriana} %")
    st.caption("Total = dientes presentes × 4 superficies (no cuenta perdidos ni sin erupcionar). "
               "Índice = superficies teñidas ÷ total × 100.")

    # 5) Tabla de hallazgos (también va al PDF)
    st.session_state.plan_tratamiento = odo.tabla_hallazgos(
        st.session_state.odo_superficies, st.session_state.odo_dientes)
    odontograma_png = odo.a_png(imagen_odo)
    if st.session_state.plan_tratamiento:
        st.markdown("**Hallazgos registrados en el odontograma**")
        st.dataframe(pd.DataFrame(st.session_state.plan_tratamiento)[["Diente", "Hallazgo", "Superficies"]],
                     use_container_width=True, hide_index=True)

    seccion("AYUDAS DIAGNÓSTICAS Y ÍNDICES", "🩻")
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
        st.metric("% Placa bacteriana (O'Leary)", f"{pct_placa_bacteriana} %")
        pronostico_gral = st.selectbox("Pronóstico", ["Seleccione...", "Favorable", "Desfavorable"], key="input_pron")

    seccion("DIAGNÓSTICOS Y PLAN GENERAL", "🧾")
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


# --- TAB 5: EVOLUCIÓN ---
with tab5:
    seccion("Evolución del Tratamiento", "📈", modulo=5)
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

# --- TAB 6: FIRMAS Y CONSENTIMIENTOS INFORMADOS ---
with tab6:
    seccion("Consentimientos Informados y Firmas Digitales", "✍️", modulo=6)
    
    seccion("DILIGENCIAMIENTO DE CONSENTIMIENTO INFORMADO", "📋")
    
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
    seccion("CARGA DE FIRMAS DIGITALES", "🖊️")
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

    # ---------------- GENERAR PDF (un solo clic) ----------------
    # Copias de lo guardado en la sesión, para usarlas en el momento del clic
    _plan_pdf = list(st.session_state.plan_tratamiento)
    _evoluciones_pdf = list(st.session_state.evoluciones)

    def construir_pdf():
        """Arma los datos y genera el PDF. Se ejecuta al hacer clic en el botón."""
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
        return generar_pdf_hc(
            datos_hc,
            _plan_pdf,
            _evoluciones_pdf,
            firma_paciente_file=file_firma_paciente,
            firma_odonto_file=file_firma_odonto,
            odontograma_png=odontograma_png
        )

    requisitos = [
        ("Nombre del paciente", "Módulo 1", bool(nombre_paciente), True),
        ("Nombre del profesional / estudiante", "Módulo 6", bool(nombre_odonto), True),
        ("N° de documento del paciente", "Módulo 1", bool(num_doc), False),
        ("Consentimiento aceptado", "Módulo 6", bool(acepta_consentimiento), False),
        ("Firma del paciente", "Módulo 6", file_firma_paciente is not None, False),
        ("Firma del profesional", "Módulo 6", file_firma_odonto is not None, False),
    ]
    listo_para_pdf = all(ok for _, _, ok, obligatorio in requisitos if obligatorio)
    tarjeta_requisitos(requisitos, listo_para_pdf)

    _doc = (num_doc or "paciente").strip().replace(" ", "_")
    nombre_pdf = f"HC_Odontologica_{_doc}_{fecha_hc.strftime('%Y-%m-%d')}.pdf"
    # Con Streamlit reciente el PDF se crea en el mismo clic de descarga (sin recargar la página);
    # en versiones antiguas se prepara antes, solo cuando ya están los datos obligatorios.
    if DESCARGA_DIFERIDA:
        datos_pdf, al_hacer_clic = construir_pdf, "ignore"
    else:
        datos_pdf, al_hacer_clic = (construir_pdf() if listo_para_pdf else b""), None
    st.download_button(
        label="📄 GENERAR Y DESCARGAR HISTORIA CLÍNICA (PDF)",
        data=datos_pdf,
        file_name=nombre_pdf,
        mime="application/pdf",
        key="btn_pdf",
        type="primary",
        disabled=not listo_para_pdf,
        on_click=al_hacer_clic,
        use_container_width=True,
    )


# ---------------- PANEL DE AVANCE (Tailwind) ----------------
def _lleno(v):
    if isinstance(v, str):
        return bool(v.strip()) and v != "Seleccione..."
    return bool(v)


def _avance(valores):
    return sum(_lleno(v) for v in valores) / len(valores) if valores else 0


avance_modulos = [
    ("Datos administrativos", _avance([hc_num, eps, nombre_paciente, tipo_doc, num_doc, sexo, direccion, telefono,
                                       estado_civil, ocupacion, tipo_plan, condicion_usuario])),
    ("Anamnesis y antecedentes", _avance([motivo, enfermedad_actual, higiene_oral_est, cepillo_dental, seda_dental,
                                          enjuagues] + list(antecedentes_dict.values()))),
    ("Examen estomatológico", _avance([obs_examen_fisico, ingesta_carbohidratos, num_comidas])),
    ("Odontograma y diagnóstico", _avance([st.session_state.odo_superficies or st.session_state.odo_dientes,
                                           diag_principal, cod_principal, pronostico_gral, plan_areas,
                                           desc_plan_tratamiento])),
    ("Evolución", _avance([st.session_state.evoluciones])),
    ("Firmas y consentimientos", _avance([consentimientos_seleccionados, acepta_consentimiento, nombre_odonto,
                                          tarjeta_prof, file_firma_paciente, file_firma_odonto])),
]
panel_avance(panel_progreso, avance_modulos, listo_pdf=bool(nombre_paciente and nombre_odonto))