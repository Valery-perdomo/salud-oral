import base64
import html
import os
from datetime import date

import pandas as pd
import streamlit as st
from streamlit_image_coordinates import streamlit_image_coordinates

import odontograma as odo
from pdf_generator import generar_pdf_hc

st.set_page_config(page_title="Historia Clínica Odontológica - San Pedro Claver", page_icon="🦷", layout="wide")

# Oculta menú y barra superior de Streamlit, y carga los estilos (incluye Tailwind compilado)
st.markdown('<style>#MainMenu, footer, [data-testid="stHeader"] {visibility: hidden;}</style>', unsafe_allow_html=True)
if os.path.exists("stilo.css"):
    st.markdown(f"<style>{open('stilo.css', encoding='utf-8').read()}</style>", unsafe_allow_html=True)

ss = st.session_state
SEL = "Seleccione..."


# ======================= COMPONENTES VISUALES (Tailwind, prefijo tw:) =======================
def _html(fragmento):
    """Streamlit toma como Markdown las líneas con sangría: se envía el HTML en una sola línea."""
    return " ".join(l.strip() for l in fragmento.splitlines() if l.strip())


def md(fragmento):
    st.markdown(_html(fragmento), unsafe_allow_html=True)


def encabezado(logo_b64):
    logo = (f'<div class="tw:shrink-0 tw:rounded-2xl tw:bg-white tw:p-3 tw:shadow-lg tw:ring-4 tw:ring-white/30 tw:transition '
            f'tw:duration-300 tw:hover:scale-105 tw:hover:-rotate-2"><img src="data:image/png;base64,{logo_b64}" '
            f'alt="Escuela de Salud San Pedro Claver" class="tw:h-16 tw:w-40 tw:object-contain"></div>') if logo_b64 else ""
    md(f"""
    <div class="tw:group tw:relative tw:mb-4 tw:overflow-hidden tw:rounded-3xl tw:bg-linear-to-r tw:from-teal-800 tw:via-teal-700
                tw:to-emerald-500 tw:px-8 tw:py-6 tw:shadow-xl tw:transition tw:duration-500 tw:hover:shadow-2xl">
      <div class="tw:pointer-events-none tw:absolute tw:-right-16 tw:-top-20 tw:size-64 tw:rounded-full tw:bg-white/10
                  tw:transition tw:duration-700 tw:group-hover:scale-125"></div>
      <div class="tw:pointer-events-none tw:absolute tw:-bottom-24 tw:right-1/3 tw:size-56 tw:rounded-full tw:bg-emerald-300/10
                  tw:transition tw:duration-700 tw:group-hover:-translate-y-4"></div>
      <div class="tw:relative tw:flex tw:flex-col tw:items-center tw:gap-5 tw:text-center tw:md:flex-row tw:md:text-left">
        {logo}
        <div class="tw:flex-1">
          <div class="tw:text-xs tw:font-semibold tw:uppercase tw:tracking-[0.25em] tw:text-emerald-100">Simulador académico</div>
          <div class="tw:text-3xl tw:font-extrabold tw:leading-tight tw:tracking-tight tw:text-white">Historia Clínica Odontológica</div>
          <div class="tw:mt-1 tw:text-sm tw:font-medium tw:text-white/90">ESCUELA DE SALUD SAN PEDRO CLAVER — Programa de Salud Oral · Sede Neiva</div>
        </div>
        <div class="tw:flex tw:flex-col tw:items-center tw:gap-2 tw:md:items-end">
          <span class="tw:inline-flex tw:items-center tw:gap-2 tw:rounded-full tw:bg-white/20 tw:px-4 tw:py-2 tw:text-xs tw:font-bold
                       tw:uppercase tw:tracking-wider tw:text-white tw:backdrop-blur tw:transition tw:hover:bg-white/30">
            <span class="tw:relative tw:flex tw:size-2.5">
              <span class="tw:absolute tw:inline-flex tw:size-full tw:animate-ping tw:rounded-full tw:bg-emerald-300 tw:opacity-75"></span>
              <span class="tw:relative tw:inline-flex tw:size-2.5 tw:rounded-full tw:bg-emerald-300"></span>
            </span>Sesión abierta</span>
          <span class="tw:text-xs tw:text-white/80">🔒 Diligenciamiento seguro</span>
        </div>
      </div>
    </div>""")


def seccion(titulo, icono, modulo=None):
    """Tarjeta de título de cada sección."""
    badge = (f'<span class="tw:rounded-full tw:bg-teal-600 tw:px-2.5 tw:py-0.5 tw:text-[0.68rem] tw:font-bold tw:tracking-wider '
             f'tw:text-white">MÓDULO {modulo}</span>') if modulo is not None else ""
    md(f"""
    <div class="tw:group tw:mt-6 tw:mb-3 tw:flex tw:items-center tw:gap-3 tw:rounded-2xl tw:border tw:border-sky-100 tw:border-l-4
                tw:border-l-teal-600 tw:bg-white tw:px-5 tw:py-3 tw:shadow-sm tw:transition tw:duration-300 tw:hover:-translate-y-0.5
                tw:hover:border-teal-200 tw:hover:shadow-md">
      <span class="tw:grid tw:size-9 tw:place-items-center tw:rounded-xl tw:bg-teal-50 tw:text-lg tw:transition tw:duration-300
                   tw:group-hover:scale-110 tw:group-hover:bg-teal-100">{icono}</span>
      {badge}
      <span class="tw:text-sm tw:font-extrabold tw:uppercase tw:tracking-wide tw:text-teal-700">{html.escape(titulo)}</span>
    </div>""")


CIRCULO = "tw:grid tw:size-6 tw:shrink-0 tw:place-items-center tw:rounded-full tw:text-xs tw:font-bold "
PILDORA = "tw:inline-flex tw:items-center tw:gap-1.5 tw:rounded-full tw:px-3 tw:py-1.5 tw:text-xs tw:font-bold "


def tarjeta_requisitos(requisitos, listo):
    """Lista de verificación antes de generar el PDF."""
    filas = ""
    for nombre, modulo, ok, obligatorio in requisitos:
        if ok:
            icono, etiqueta = f'<span class="{CIRCULO}tw:bg-emerald-500 tw:text-white">✓</span>', ""
        elif obligatorio:
            icono = f'<span class="{CIRCULO}tw:bg-rose-100 tw:text-rose-600">!</span>'
            etiqueta = ('<span class="tw:rounded-full tw:bg-rose-50 tw:px-2 tw:py-0.5 tw:text-[0.62rem] tw:font-bold '
                        'tw:text-rose-600">Obligatorio</span>')
        else:
            icono = f'<span class="{CIRCULO}tw:bg-slate-100 tw:text-slate-400">○</span>'
            etiqueta = '<span class="tw:text-[0.62rem] tw:font-semibold tw:text-slate-400">Recomendado</span>'
        filas += f"""
        <div class="tw:flex tw:items-center tw:gap-3 tw:rounded-xl tw:border tw:border-slate-100 tw:bg-white tw:px-3 tw:py-2
                    tw:transition tw:duration-200 tw:hover:border-teal-200 tw:hover:bg-teal-50/40">
          {icono}
          <div class="tw:flex-1"><div class="tw:text-sm tw:font-semibold tw:text-slate-700">{html.escape(nombre)}</div>
            <div class="tw:text-[0.68rem] tw:text-slate-400">{modulo}</div></div>
          {etiqueta}
        </div>"""
    titulo, color = (("✅ Todo listo: haz clic en el botón y el PDF se descarga de una vez",
                      "tw:border-emerald-200 tw:bg-emerald-50/60 tw:text-emerald-800") if listo else
                     ("⚠️ Completa los datos obligatorios para habilitar el PDF", "tw:border-rose-200 tw:bg-rose-50/60 tw:text-rose-700"))
    md(f"""<div class="tw:mt-2 tw:mb-4 tw:rounded-2xl tw:border tw:p-4 {color}">
      <div class="tw:mb-3 tw:text-sm tw:font-bold">{titulo}</div>
      <div class="tw:grid tw:gap-2 tw:md:grid-cols-2 tw:xl:grid-cols-3">{filas}</div></div>""")


MODULOS = ["1. Datos Administrativos", "2. Anamnesis y Antecedentes", "3. Examen Estomatológico",
           "4. Odontograma y Diag.", "5. Evolución", "6. Firmas y Consentimientos"]
ICONOS_MODULO = ["🗂️", "🗣️", "🔎", "🦷", "📈", "✍️"]
NAV_KEY = "nav_modulos"  # Pestaña abierta; se cambia haciendo clic en las tarjetas del panel


def ir_a_modulo(etiqueta):
    ss[NAV_KEY] = etiqueta


def panel_avance(contenedor, modulos, listo_pdf):
    """Anillo con el avance total y una tarjeta por módulo; cada tarjeta abre su módulo."""
    total = round(100 * sum(p for _, p in modulos) / len(modulos))
    estado = (f'<span class="{PILDORA}tw:bg-emerald-100 tw:text-emerald-700">✅ Lista para generar el PDF</span>' if listo_pdf
              else f'<span class="{PILDORA}tw:bg-amber-100 tw:text-amber-700">✏️ En diligenciamiento</span>')
    with contenedor.container(key="panel_avance"):
        md(f"""
        <div class="tw:flex tw:flex-wrap tw:items-center tw:gap-4">
          <div class="tw:grid tw:size-16 tw:shrink-0 tw:place-items-center tw:rounded-full"
               style="background:conic-gradient(#0d9488 {total * 3.6}deg, #e2e8f0 0deg)">
            <div class="tw:grid tw:size-12 tw:place-items-center tw:rounded-full tw:bg-white tw:text-sm tw:font-extrabold
                        tw:text-teal-700">{total}%</div>
          </div>
          <div class="tw:min-w-48 tw:flex-1">
            <div class="tw:text-base tw:font-bold tw:text-slate-800">Avance de la historia clínica</div>
            <div class="tw:text-xs tw:text-slate-500">{sum(p >= 1 for _, p in modulos)} de {len(modulos)} módulos completos ·
              haz clic en un módulo para abrirlo</div>
          </div>
          {estado}
        </div>""")
        for i, ((nombre, p), col) in enumerate(zip(modulos, st.columns(len(modulos))), start=1):
            pct = round(100 * p)
            if pct >= 100:
                linea, fondo, relleno, chip = ("tw:bg-emerald-400", "tw:bg-emerald-50", "tw:bg-emerald-500",
                                               f'<span class="{CIRCULO}tw:bg-emerald-500 tw:text-white">✓</span>')
            elif pct > 0:
                linea, fondo, relleno, chip = ("tw:bg-amber-400", "tw:bg-amber-50", "tw:bg-amber-400",
                                               '<span class="tw:rounded-full tw:bg-amber-100 tw:px-2 tw:py-0.5 tw:text-[0.65rem] '
                                               f'tw:font-bold tw:text-amber-700">{pct}%</span>')
            else:
                linea, fondo, relleno, chip = ("tw:bg-slate-200", "tw:bg-slate-100", "tw:bg-slate-300",
                                               '<span class="tw:text-[0.65rem] tw:font-semibold tw:text-slate-400">Pendiente</span>')
            activa = " tarjeta-activa" if MODULOS[i - 1] == ss.get(NAV_KEY, MODULOS[0]) else ""
            with col.container(key=f"tarjeta_{i}"):
                md(f"""
                <div class="tarjeta-modulo{activa} tw:relative tw:overflow-hidden tw:rounded-2xl tw:border tw:border-slate-200
                            tw:bg-white tw:p-3.5 tw:shadow-sm">
                  <div class="tw:absolute tw:inset-x-0 tw:top-0 tw:h-1 {linea}"></div>
                  <div class="tw:flex tw:items-center tw:justify-between">
                    <span class="tarjeta-icono tw:grid tw:size-10 tw:place-items-center tw:rounded-xl tw:text-xl {fondo}">{ICONOS_MODULO[i - 1]}</span>
                    {chip}
                  </div>
                  <div class="tw:mt-2 tw:text-[0.62rem] tw:font-bold tw:uppercase tw:tracking-widest tw:text-slate-400">Módulo {i}</div>
                  <div class="tw:min-h-9 tw:text-sm tw:font-bold tw:leading-tight tw:text-slate-800">{html.escape(nombre)}</div>
                  <div class="tw:mt-2 tw:h-1.5 tw:overflow-hidden tw:rounded-full tw:bg-slate-100">
                    <div class="tw:h-full tw:rounded-full tw:transition-all tw:duration-700 {relleno}" style="width:{pct}%"></div>
                  </div>
                </div>""")
                # Botón invisible que cubre toda la tarjeta (ver stilo.css)
                st.button(f"Abrir {nombre}", key=f"nav_{i}", on_click=ir_a_modulo, args=(MODULOS[i - 1],))


# ======================= ENCABEZADO, ESTADO Y PESTAÑAS =======================
logo_b64 = base64.b64encode(open("logo.png", "rb").read()).decode() if os.path.exists("logo.png") else ""
encabezado(logo_b64)
panel_progreso = st.empty()  # Se llena al final, cuando ya se conocen todos los datos

# Odontograma: {"17-arriba": "Caries"} por superficie y {"17": "Endodoncia indicada"} por diente.
# odonto_version renueva el lienzo tras cada cambio; ultimo_click_odonto evita marcas duplicadas.
for clave, inicial in {"evoluciones": [], "plan_tratamiento": [], "odo_superficies": {}, "odo_dientes": {},
                       "odo_historial": [], "convencion_odontograma": "Caries", "odonto_version": 0,
                       "ultimo_click_odonto": None}.items():
    ss.setdefault(clave, inicial)

# Todas las pestañas se ejecutan (así el PDF tiene todos los datos); la visible la eligen las tarjetas.
try:
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(MODULOS, key=NAV_KEY, on_change="rerun")
    st.markdown("""<style>.stTabs [role="tablist"], .stTabs [data-testid="stTab"], [data-testid="stTabsScrollLeft"],
        [data-testid="stTabsScrollRight"], .stTabs [data-baseweb="tab-list"], .stTabs [data-baseweb="tab-border"],
        .stTabs [data-baseweb="tab-highlight"] { display: none !important; }</style>""", unsafe_allow_html=True)
except TypeError:  # Streamlit antiguo sin esta opción: se dejan las pestañas visibles
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(MODULOS)


def radio(etiqueta, opciones, key):
    return st.radio(etiqueta, opciones, index=None, horizontal=True, key=key)


# ======================= TAB 1: DATOS ADMINISTRATIVOS E IDENTIFICACIÓN =======================
with tab1:
    seccion("Datos Administrativos de la Consulta", "🗂️", modulo=0)
    c1, c2, c3 = st.columns(3)
    hc_num = c1.text_input("HISTORIA CLÍNICA N°", value="HC-2026-001", key="input_hc_num")
    fecha_hc = c2.date_input("FECHA DE ATENCIÓN", value=date.today(), min_value=date(2020, 1, 1),
                             max_value=date(2030, 12, 31), key="input_fecha_hc")
    eps = c3.text_input("EPS DEL PACIENTE", value="", placeholder="Escribe la EPS...", key="input_eps")

    seccion("Datos Personales del Paciente", "👤", modulo=1)
    seccion("IDENTIFICACIÓN E INFORMACIÓN GENERAL", "🪪")
    c1, c2, c3 = st.columns(3)
    with c1:
        nombre_paciente = st.text_input("Nombre del Paciente (Completo)", value="", placeholder="Nombre completo...", key="input_nombre")
        tipo_doc = st.selectbox("Tipo de Documento", [SEL, "CC", "TI", "RC", "MS", "CE", "PA", "ASI"], key="input_tipodoc")
        sexo = radio("Sexo", ["Hombre", "Mujer"], "input_sexo")
        tipo_plan = st.selectbox("Tipo de Plan", [SEL, "POS", "POS SUBS.", "PREPAGO", "OTRO"], key="input_tipplan")
    with c2:
        num_doc = st.text_input("N° de Documento", value="", placeholder="Número de documento...", key="input_numdoc")
        fecha_nac = st.date_input("Fecha de Nacimiento (DD/MM/AAAA)", value=date(2000, 1, 1), min_value=date(1920, 1, 1),
                                  max_value=date.today(), format="DD/MM/YYYY", key="input_fechanac")
        hoy = date.today()
        edad = hoy.year - fecha_nac.year - ((hoy.month, hoy.day) < (fecha_nac.month, fecha_nac.day))
        ss["input_edad_calc"] = f"{edad} años"
        st.text_input("Edad (calculada)", key="input_edad_calc", disabled=True)
        condicion_usuario = st.selectbox("Condición del Usuario", [SEL, "COTIZANTE", "BENEFICIARIO", "PENSIONADO", "OTRO"], key="input_condicion")
    with c3:
        direccion = st.text_input("Dirección de Vivienda", value="", placeholder="Dirección...", key="input_dir")
        telefono = st.text_input("Teléfono de Contacto", value="", placeholder="Teléfono...", key="input_tel")
        ciudad_depto = st.selectbox("Ciudad / Departamento", [
            "Neiva / Huila", "Bogotá D.C.", "Medellín / Antioquia", "Cali / Valle del Cauca", "Barranquilla / Atlántico",
            "Cartagena / Bolívar", "Bucaramanga / Santander", "Ibagué / Tolima", "Villavicencio / Meta", "Florencia / Caquetá",
            "Garzón / Huila", "Pitalito / Huila", "La Plata / Huila", "Otro / Fuera de Colombia"], key="input_ciudad")
        estado_civil = st.selectbox("Estado Civil", [SEL, "Soltero", "Casado", "Otro"], key="input_estcivil")
        ocupacion = st.text_input("Ocupación", value="", placeholder="Ocupación...", key="input_ocupacion")

    seccion("ACOMPAÑANTE Y RESPONSABLE", "👥")
    c1, c2 = st.columns(2)
    nombre_acomp = c1.text_input("Nombre del Acompañante", value="", key="input_acomp")
    tel_acomp = c1.text_input("Teléfono Acompañante", value="", key="input_telacomp")
    nombre_resp = c2.text_input("Nombre del Responsable", value="", key="input_resp")
    tel_resp = c2.text_input("Teléfono Responsable", value="", key="input_telresp")

# ======================= TAB 2: ANAMNESIS Y ANTECEDENTES =======================
with tab2:
    seccion("Anamnesis y Antecedentes Médicos", "🗣️", modulo=2)
    motivo = st.text_area("Motivo de Consulta (Textual del paciente)", value="", placeholder="Ej: Presenta dolor agudo en molar inferior...", key="input_motivo")
    enfermedad_actual = st.text_area("Historia de la Enfermedad Actual", value="", placeholder="Describa el inicio, frecuencia y evolución...", key="input_enfermedad")

    seccion("ANTECEDENTES MÉDICOS (DILIGENCIAR CADA ÍTEM)", "📋")
    antecedentes = ["1. Tratamiento médico", "2. Ingestión medicamentos", "3. Reacciones alérgicas (Anestesia/Antibióticos)",
                    "4. Hemorragias", "5. Irradiaciones", "6. Sinusitis", "7. Enfermedad respiratoria", "8. Cardiopatías",
                    "9. Diabetes", "10. Fiebre reumática", "11. Hepatitis", "12. Hipertensión", "13. Embarazo",
                    "14. Enfermedades renales", "15. Enfermedades gastrointestinales", "16. Órganos de los sentidos", "Otros"]
    cols = st.columns(2)
    antecedentes_dict = {}
    for i, item in enumerate(antecedentes):
        with cols[i % 2]:
            antecedentes_dict[item] = radio(item, ["NO", "SI", "NO SABE"], f"ant_{i}")
    obs_antecedentes = st.text_area("Observaciones de Antecedentes Médicos", value="", key="input_obsant")

    seccion("HIGIENE ORAL Y SALUD BUCAL", "🪥")
    c1, c2, c3 = st.columns(3)
    with c1:
        u_visita_fecha = st.date_input("Última visita al Odontólogo", value=date.today(), key="input_uvisita")
        u_visita_motivo = st.text_input("Motivo última visita", value="", key="input_motivovisita")
        higiene_oral_est = radio("Higiene Oral General", ["Bueno (B)", "Regular (R)", "Malo (M)"], "input_higoral")
    with c2:
        cepillo_dental = radio("¿Usa Cepillo Dental?", ["SI", "NO"], "input_cepillo")
        veces_al_dia = st.number_input("¿Cuántas veces al día?", min_value=0, max_value=10, value=0, key="input_veces")
    with c3:
        seda_dental = radio("¿Usa Seda Dental?", ["SI", "NO"], "input_seda")
        enjuagues = radio("¿Usa Enjuagues Bucales?", ["SI", "NO"], "input_enj")

# ======================= TAB 3: EXAMEN ESTOMATOLÓGICO =======================
with tab3:
    seccion("Examen Físico Estomatológico", "🔎", modulo=3)
    seccion("TEJIDOS BLANDOS Y ESTRUCTURAS BUCALES (MARCAR SI PRESENTA ANORMALIDAD)", "👄")
    elementos = ["1. A.T.M.", "2. Labios", "3. Lengua", "4. Paladar", "5. Piso de boca", "6. Carrillos", "7. Glándulas salivares",
                 "8. Maxilares", "9. Senos maxilares", "10. Músculos masticadores", "11. Ganglios", "12. Oclusión",
                 "13. Frenillos", "14. Mucosas", "15. Encías", "16. Amígdalas"]
    cols = st.columns(2)
    estomatologico_dict = {}
    for i, elem in enumerate(elementos):
        with cols[i % 2]:
            estomatologico_dict[elem] = st.checkbox(f"{elem} (Anormal)", key=f"est_{i}")

    seccion("HÁBITOS NOCIVOS", "🚭")
    habitos = ["Bruxismo", "Deglución atípica", "Empuje lingual", "Fumar", "Morder objetos", "Onicofagia",
               "Respirador oral", "Uso palillos", "Succión digital", "Otros"]
    cols = st.columns(2)
    habitos_dict = {}
    for i, hab in enumerate(habitos):
        with cols[i % 2]:
            habitos_dict[hab] = st.checkbox(hab, key=f"hab_{i}")

    seccion("EXAMEN DENTAL, PERIODONTAL Y HALLAZGOS GENERALES", "🦷")
    # (título de columna, [(etiqueta del checkbox, key, nombre en el PDF)])
    grupos_examen = [
        ("Examen Dental", [("Supernumerarios", "chk_sup", "Supernumerarios"), ("Abrasión", "chk_abr", "Abrasión"),
                           ("Manchas - Cambios de color", "chk_man", "Manchas"),
                           ("Patología pulpar - Abscesos", "chk_pul", "Pat. Pulpar")]),
        ("Examen Periodontal", [("Bolsas - Movilidad", "chk_bol", "Bolsas"), ("Placa blanda", "chk_pla", "Placa"),
                                ("Cálculos", "chk_cal", "Cálculos")]),
        ("Hallazgos Generales", [("Ortodoncia", "chk_ort", "Ortodoncia"), ("Prótesis", "chk_pro", "Prótesis")]),
    ]
    resumen_examen = []  # "Supernumerarios: SI, Abrasión: NO, ..." por cada grupo
    for col, (titulo, items) in zip(st.columns(3), grupos_examen):
        with col:
            st.markdown(f"**{titulo}**")
            resumen_examen.append(", ".join(f"{pdf}: {'SI' if st.checkbox(lbl, key=k) else 'NO'}" for lbl, k, pdf in items))
    obs_examen_fisico = st.text_area("Observaciones del Examen Físico", value="", key="input_obsexam")

    seccion("HÁBITOS ALIMENTICIOS", "🍎")
    c1, c2 = st.columns(2)
    with c1:
        ingesta_carbohidratos = radio("Ingesta de Carbohidratos (Azúcares / Harinas)", ["Baja", "Media", "Alta (5-7)"], "input_carb")
    with c2:
        num_comidas = radio("Número de Comidas Diarias", ["< 3", "3 - 4", "> 4"], "input_com")

# ======================= TAB 4: ODONTOGRAMA Y DIAGNÓSTICOS =======================
with tab4:
    seccion("Odontograma y Registro FDI", "🦷", modulo=4)
    seccion("ESQUEMA DENTAL Y CONVENCIONES CLÍNICAS", "🗺️")
    denticion = st.radio("Tipo de dentición", ["Permanente", "Temporal", "Mixta"], horizontal=True, key="input_dent")

    # 1) Barra de convenciones: un ícono por signo (al pasar el mouse sale el nombre)
    nombres_conv = list(odo.CONVENCIONES)
    for inicio in range(0, len(nombres_conv), 12):
        for col, nombre in zip(st.columns(12), nombres_conv[inicio:inicio + 12]):
            with col:
                if st.button(odo.CONVENCIONES[nombre]["icono"], key=f"conv_{nombre}", help=nombre, use_container_width=True,
                             type="primary" if nombre == ss.convencion_odontograma else "secondary"):
                    ss.convencion_odontograma = nombre
                    st.rerun()

    conv_activa = ss.convencion_odontograma
    info_activa = odo.CONVENCIONES[conv_activa]
    como = {"superficie": "toca la superficie del diente", "diente": "toca cualquier parte del diente (se marca completo)",
            "borrar": "toca una superficie o diente para limpiarlo"}[info_activa["tipo"]]
    st.markdown(f"{info_activa['icono']} **{conv_activa}** — {como}")

    def guardar_para_deshacer():
        ss.odo_historial.append((dict(ss.odo_superficies), dict(ss.odo_dientes)))

    def redibujar():
        ss.odonto_version += 1
        st.rerun()

    # 2) Dibujo del odontograma (centrado) y detección del clic
    imagen_odo = odo.dibujar(denticion, ss.odo_superficies, ss.odo_dientes)
    clave_canvas = f"odontograma_canvas_{ss.odonto_version}"
    iframe = 'iframe[title="streamlit_image_coordinates.streamlit_image_coordinates"]'
    st.markdown(f"""<style>
        div[data-testid="stElementContainer"]:has({iframe}), div.element-container:has({iframe}) {{
            display: flex; justify-content: center; width: 100% !important; }}
        {iframe} {{ width: {odo.ANCHO}px !important; max-width: 100%; margin: 0 auto; display: block; }}
    </style>""", unsafe_allow_html=True)
    coordenada = streamlit_image_coordinates(imagen_odo, width=odo.ANCHO, key=clave_canvas)

    if coordenada:
        firma_click = (clave_canvas, coordenada["x"], coordenada["y"], coordenada.get("unix_time"))
        if ss.ultimo_click_odonto != firma_click:
            ss.ultimo_click_odonto = firma_click
            escala = odo.ANCHO / (coordenada.get("width") or odo.ANCHO)  # por si el navegador achicó la imagen
            diente, sup = odo.detectar(denticion, coordenada["x"] * escala, coordenada["y"] * escala)
            if diente is not None:
                guardar_para_deshacer()
                tipo = info_activa["tipo"]
                if tipo == "borrar":
                    if str(diente) in ss.odo_dientes:
                        ss.odo_dientes.pop(str(diente))
                    else:
                        ss.odo_superficies.pop(f"{diente}-{sup}", None)
                else:  # tocar de nuevo con la misma convención = quitar
                    marcas, clave = ((ss.odo_superficies, f"{diente}-{sup}") if tipo == "superficie"
                                     else (ss.odo_dientes, str(diente)))
                    if marcas.get(clave) == conv_activa:
                        marcas.pop(clave)
                    else:
                        marcas[clave] = conv_activa
                redibujar()

    # 3) Deshacer / borrar todo
    c1, c2 = st.columns(2)
    if c1.button("↩️ Deshacer última marca", key="deshacer_marca_odontograma", use_container_width=True,
                 disabled=not ss.odo_historial):
        ss.odo_superficies, ss.odo_dientes = ss.odo_historial.pop()
        redibujar()
    if c2.button("🧹 Borrar todo el odontograma", key="borrar_marcas_odontograma", use_container_width=True):
        guardar_para_deshacer()
        ss.odo_superficies, ss.odo_dientes = {}, {}
        redibujar()

    # 4) Índice O'Leary automático
    total_sup, sup_tenidas, pct_placa_bacteriana = odo.indice_oleary(denticion, ss.odo_superficies, ss.odo_dientes)
    st.markdown("**Índice de placa O'Leary** (se marca con el ícono amarillo de placa bacteriana)")
    o1, o2, o3 = st.columns(3)
    o1.metric("Total superficies", total_sup)
    o2.metric("Superficies teñidas", sup_tenidas)
    o3.metric("Índice O'Leary", f"{pct_placa_bacteriana} %")
    st.caption("Total = dientes presentes × 4 superficies (no cuenta perdidos ni sin erupcionar). "
               "Índice = superficies teñidas ÷ total × 100.")

    # 5) Tabla de hallazgos (también va al PDF)
    ss.plan_tratamiento = odo.tabla_hallazgos(ss.odo_superficies, ss.odo_dientes)
    odontograma_png = odo.a_png(imagen_odo)
    if ss.plan_tratamiento:
        st.markdown("**Hallazgos registrados en el odontograma**")
        st.dataframe(pd.DataFrame(ss.plan_tratamiento)[["Diente", "Hallazgo", "Superficies"]], use_container_width=True, hide_index=True)

    seccion("AYUDAS DIAGNÓSTICAS Y ÍNDICES", "🩻")
    rx1, rx2, rx3, rx4 = st.columns(4)
    rx_periapical = rx1.number_input("Rx Periapical (Placas)", min_value=0, value=0, key="input_rxper")
    rx_oclusal = rx1.number_input("Rx Oclusal (Placas)", min_value=0, value=0, key="input_rxocl")
    rx_panoramica = rx2.number_input("Rx Panorámica", min_value=0, value=0, key="input_rxpan")
    rx_otra = rx2.text_input("Otra Radiografía", value="", key="input_rxotra")
    placas_tomadas = rx3.number_input("Placas Tomadas", min_value=0, value=0, key="input_pltom")
    placas_danadas = rx3.number_input("Placas Dañadas", min_value=0, value=0, key="input_pldan")
    rx4.metric("% Placa bacteriana (O'Leary)", f"{pct_placa_bacteriana} %")
    pronostico_gral = rx4.selectbox("Pronóstico", [SEL, "Favorable", "Desfavorable"], key="input_pron")

    seccion("DIAGNÓSTICOS Y PLAN GENERAL", "🧾")
    c1, c2 = st.columns(2)
    diag_presuntivo = c1.text_input("Diagnóstico Presuntivo", value="", key="input_diagpres")
    diag_principal = c1.text_input("Diagnóstico Principal Definitivo", value="", key="input_diagprinc")
    cod_principal = c1.text_input("Código CIE-10 Principal", value="", key="input_codprinc")
    diag_secundario = c2.text_input("Diagnóstico Secundario", value="", key="input_diagsec")
    cod_secundario = c2.text_input("Código CIE-10 Secundario", value="", key="input_codsec")
    citas_programar = c2.number_input("No. Citas a Programar", min_value=1, value=1, key="input_citasprog")
    st.markdown("**Áreas del Plan de Tratamiento:**")
    plan_areas = st.multiselect("Marcar Especialidades Requeridas", ["Promoción y Prevención", "Operatoria", "Endodoncia",
                                "Cirugía", "Rehabilitación", "Otro"], default=[], key="input_planareas")
    desc_plan_tratamiento = st.text_area("Descripción Detallada del Plan de Tratamiento", value="", key="input_descplan")

# ======================= TAB 5: EVOLUCIÓN =======================
with tab5:
    seccion("Evolución del Tratamiento", "📈", modulo=5)
    c1, c2, c3 = st.columns([1, 1, 2])
    fecha_ev = c1.date_input("Fecha Tratamiento", value=date.today(), key="input_fechaev")
    diente_ev = c1.text_input("Diente / Sitio / Cavidad", value="", key="input_dienteev")
    tratamiento_ejecutado = c2.text_input("Tratamiento Ejecutado en Sesión", value="", key="input_tratejec")
    with c3:
        st.write("")
        st.write("")
        if st.button("📝 REGISTRAR EVOLUCIÓN") and tratamiento_ejecutado:
            ss.evoluciones.append({"Fecha y Hora": fecha_ev.strftime("%Y-%m-%d"), "Diente/Sitio": diente_ev,
                                   "Tratamiento Ejecutado": tratamiento_ejecutado})
            st.success("Evolución guardada.")
    if ss.evoluciones:
        st.write("---")
        st.dataframe(pd.DataFrame(ss.evoluciones), use_container_width=True)

# ======================= TAB 6: CONSENTIMIENTOS, FIRMAS Y PDF =======================
with tab6:
    seccion("Consentimientos Informados y Firmas Digitales", "✍️", modulo=6)
    seccion("DILIGENCIAMIENTO DE CONSENTIMIENTO INFORMADO", "📋")
    CI_HIGIENE, CI_FLUOR, CI_RASPAJE = ("Consentimiento Informado para Higiene Oral",
                                        "Consentimiento Informado para Aplicación de Flúor Barniz",
                                        "Consentimiento Informado para Raspaje Supragingival")
    consentimientos_seleccionados = st.multiselect("Seleccione los consentimientos que desea diligenciar:",
                                                   [CI_HIGIENE, CI_FLUOR, CI_RASPAJE], default=[], key="input_tipocons")
    aceptaciones, obs_adicionales = {}, []
    fecha_proxima_fluor, instrumentos_usados = None, []
    obs_higiene = obs_fluor = obs_raspaje = reacciones_previas_fluor = zonas_raspaje = ""

    def datos_paciente(con_edad=True):
        """Línea con nombre, documento, edad y fecha que encabeza cada consentimiento."""
        edad_txt = f" &nbsp;&nbsp;|&nbsp;&nbsp; **Edad:** {edad} años" if con_edad else ""
        st.markdown(f"**Nombre y Apellido:** {nombre_paciente or '_______________'} &nbsp;&nbsp;|&nbsp;&nbsp; "
                    f"**Documento:** {num_doc or '_______________'}{edad_txt}  \n**Fecha de Atención:** {fecha_hc.strftime('%Y-%m-%d')}")

    if CI_HIGIENE in consentimientos_seleccionados:
        st.info("ℹ️ **Procedimiento:** Eliminación de placa bacteriana, manchas y cálculos superficiales mediante el uso de instrumentos manuales y/o mecánicos con el fin de mejorar la salud bucal y prevenir enfermedades como gingivitis y periodontitis.")
        with st.expander("📄 Ver y Editar Datos del Consentimiento (Higiene Oral)", expanded=True):
            datos_paciente()
            obs_higiene = st.text_area("Observaciones particulares / Comentarios adicionales del procedimiento:", value="",
                                       placeholder="Ej: Paciente presenta ligera sensibilidad previa en cuadrante 2...", key="obs_ho")
            st.markdown("""
            **Posibles efectos secundarios o molestias explicadas:**
            * Sensibilidad dental transitoria con estímulos fríos o calientes.
            * Sangrado o irritación leve en las encías.
            * Inflamación o enrojecimiento gingival pasajero.
            * Molestias al masticar o al cepillarse durante las primeras horas posteriores a la atención.

            *El paciente declara haber recibido la información completa sobre el procedimiento, sus beneficios, riesgos y cuidados posteriores, y manifiesta estar de acuerdo con su realización.*
            """)
        aceptaciones["higiene"] = st.checkbox("El paciente y/o acudiente declara haber leído, comprendido y ACEPTA la realización de la Higiene Oral.", key="chk_acp1")
        obs_adicionales.append(obs_higiene)

    if CI_FLUOR in consentimientos_seleccionados:
        st.info("ℹ️ **Procedimiento:** Aplicación preventiva de flúor barniz en superficies dentarias para retardar y detener la caries dental. Población objeto: niños, niñas y jóvenes entre 1 y 17 años (mínimo 2 veces al año, cada 6 meses).")
        with st.expander("📄 Ver y Editar Datos del Consentimiento (Aplicación de Flúor)", expanded=True):
            datos_paciente()
            c1, c2 = st.columns(2)
            fecha_proxima_fluor = c1.date_input("Fecha programada para próxima aplicación (6 meses):", value=date.today(), key="input_proxfluor")
            reacciones_previas_fluor = c2.text_input("Antecedentes de alergia/reacción a barniz:", value="", key="input_reacfluor")
            obs_fluor = st.text_area("Notas o recomendaciones específicas adicionadas:", value="",
                                     placeholder="Ej: Aplicación focalizada en molares superiores...", key="obs_fl")
            st.markdown("""
            **Información Importante:**
            - El secado rápido del barniz libera de forma lenta y continua iones de fluoruro cubriendo el esmalte dental para reducir la desmineralización.
            - **Cambio de color:** Puede presentarse un leve cambio temporal en el color del diente debido al tono del barniz.
            - **Cuidados posteriores (Durante las primeras 4 horas):** Evitar alimentos duros o pegajosos, productos con alcohol, enjuagues o bebidas calientes. Preferiblemente realizar el cepillado dental hasta la mañana siguiente.
            """)
        aceptaciones["fluor"] = st.checkbox("El paciente y/o acudiente declara haber sido informado de los riesgos/cuidados y ACEPTA la aplicación de flúor barniz.", key="chk_acp2")
        obs_adicionales.append(obs_fluor)

    if CI_RASPAJE in consentimientos_seleccionados:
        st.info("ℹ️ **Procedimiento:** Eliminación mecánica de depósitos calcificados de placa bacteriana (cálculos/sarro) mediante instrumentos manuales, sónicos o ultrasónicos (frecuencia sugerida: 1 a 2 veces por año).")
        with st.expander("📄 Ver y Editar Datos del Consentimiento (Raspaje Supragingival)", expanded=True):
            datos_paciente(con_edad=False)
            c1, c2 = st.columns(2)
            instrumentos_usados = c1.multiselect("Instrumental a emplear:", ["Instrumentos Manuales", "Instrumentos Sónicos",
                                                 "Instrumentos Ultrasónicos"], default=[], key="input_inst")
            zonas_raspaje = c2.text_input("Sectores / Cuadrantes a tratar:", value="", key="input_zonasrasp")
            obs_raspaje = st.text_area("Observaciones o hallazgos adicionales antes del procedimiento:", value="",
                                       placeholder="Ej: Se evidencia sangrado gingival en sector anterior...", key="obs_rs")
            st.markdown("""
            **1. Objetivos y Beneficios:** Prevenir enfermedades periodontal/gingivitis, disminuir la halitosis y mejorar la salud bucal.
            **2. Riesgos Informados:** Sensibilidad dental temporal al frío/calor, pequeños sangrados, molestias leves o irritación gingival pasajera.
            **3. Riesgos de no realizarlo:** Acumulación de sarro, riesgo de gingivitis, periodontitis, movilidad y pérdida de piezas dentales.

            *Autorizo de manera libre y voluntaria la realización del procedimiento de raspaje supragingival.*
            """)
        aceptaciones["raspaje"] = st.checkbox("El paciente declara haber comprendido la información y AUTORIZA de manera libre y voluntaria el Raspaje Supragingival.", key="chk_acp3")
        obs_adicionales.append(obs_raspaje)

    tipo_consentimiento = ", ".join(consentimientos_seleccionados) or "Ninguno / No aplica para esta consulta"
    acepta_consentimiento = bool(aceptaciones) and all(aceptaciones.values())
    st.write("---")

    seccion("CARGA DE FIRMAS DIGITALES", "🖊️")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Firma del Paciente / Acompañante**")
        file_firma_paciente = st.file_uploader("Adjuntar firma del paciente (PNG, JPG, PDF)", type=["png", "jpg", "jpeg", "pdf"], key="file_pac")
        if file_firma_paciente and file_firma_paciente.type != "application/pdf":
            st.image(file_firma_paciente, width=160)
    with c2:
        st.markdown("**Firma del Higienista / Estudiante / Odontólogo**")
        nombre_odonto = st.text_input("Nombre del Profesional / Estudiante", value="", key="input_nomodo")
        tarjeta_prof = st.text_input("Registro / Código Profesional", value="", key="input_regprof")
        file_firma_odonto = st.file_uploader("Adjuntar firma del profesional (PNG, JPG, PDF)", type=["png", "jpg", "jpeg", "pdf"], key="file_odo")
        if file_firma_odonto and file_firma_odonto.type != "application/pdf":
            st.image(file_firma_odonto, width=160)
    st.write("---")

    # ---------------- GENERAR PDF (un solo clic) ----------------
    plan_pdf, evoluciones_pdf = list(ss.plan_tratamiento), list(ss.evoluciones)  # copias para el momento del clic

    def opcion(valor, defecto="NO ESPECIFICADO"):
        return valor if valor and valor != SEL else defecto

    def construir_pdf():
        """Arma los datos y genera el PDF. Se ejecuta al hacer clic en el botón."""
        datos_hc = {
            "Fecha de Atención": fecha_hc.strftime("%Y-%m-%d"), "Historia Clínica N°": hc_num, "EPS": eps,
            "Tipo Plan": opcion(tipo_plan), "Condición Usuario": opcion(condicion_usuario), "Paciente": nombre_paciente,
            "Tipo Doc": opcion(tipo_doc, "CC"), "Documento Paciente": num_doc, "Sexo": opcion(sexo), "Edad": edad,
            "Estado Civil": opcion(estado_civil), "Ocupación": ocupacion, "Fecha Nacimiento": fecha_nac.strftime("%Y-%m-%d"),
            "Teléfono": telefono, "Dirección": direccion, "Ciudad/Departamento": ciudad_depto,
            "Acompañante": f"{nombre_acomp} (Tel: {tel_acomp})" if nombre_acomp else "Ninguno",
            "Responsable": f"{nombre_resp} (Tel: {tel_resp})" if nombre_resp else "Ninguno",
            "Motivo de Consulta": motivo, "Enfermedad Actual": enfermedad_actual, "Antecedentes": antecedentes_dict,
            "Obs Antecedentes": obs_antecedentes,
            "Higiene Oral": f"Visita: {u_visita_fecha} | Motivo: {u_visita_motivo} | Estado: {higiene_oral_est} | Cepillo: "
                            f"{cepillo_dental} ({veces_al_dia}/día) | Seda: {seda_dental} | Enjuague: {enjuagues}",
            "Estomatologico": estomatologico_dict, "Habitos": habitos_dict,
            "Dental": resumen_examen[0], "Periodontal": resumen_examen[1], "Hallazgos Gen": resumen_examen[2],
            "Obs Examen Fisico": obs_examen_fisico,
            "Alimenticios": f"Carbohidratos: {ingesta_carbohidratos} | Comidas/día: {num_comidas}",
            "Dentadura": f"Dentición {denticion}",
            "Radiografias": f"Periapical: {rx_periapical}, Oclusal: {rx_oclusal}, Panorámica: {rx_panoramica}, Otra: {rx_otra} "
                            f"| Tomadas: {placas_tomadas}, Dañadas: {placas_danadas}",
            "Indices": f"Placa Bacteriana: {pct_placa_bacteriana}% | Pronóstico: {pronostico_gral}",
            "Diags": f"Presuntivo: {diag_presuntivo} | Principal: {diag_principal} ({cod_principal}) | "
                     f"Secundario: {diag_secundario} ({cod_secundario})",
            "Plan Resumen": f"Áreas: {', '.join(plan_areas)} | Citas: {citas_programar} | Detalle: {desc_plan_tratamiento}",
            "Consentimiento Tipo": tipo_consentimiento, "Consentimientos Seleccionados": tipo_consentimiento,
            "Consentimiento Aceptado": "SÍ" if acepta_consentimiento else "NO / NO APLICA",
            "Proxima Cita Fluor": fecha_proxima_fluor.strftime("%Y-%m-%d") if fecha_proxima_fluor else "N/A",
            "Obs Higiene Oral": obs_higiene, "Obs Fluor": obs_fluor, "Obs Raspaje": obs_raspaje,
            "Obs Consentimiento Adicional": " | ".join(obs_adicionales), "Reacciones Previas Fluor": reacciones_previas_fluor,
            "Instrumentos Raspaje": ", ".join(instrumentos_usados) or "N/A", "Zonas Raspaje": zonas_raspaje,
            "Odontólogo Tratante": nombre_odonto, "Código/Registro": tarjeta_prof,
        }
        return generar_pdf_hc(datos_hc, plan_pdf, evoluciones_pdf, firma_paciente_file=file_firma_paciente,
                              firma_odonto_file=file_firma_odonto, odontograma_png=odontograma_png)

    requisitos = [  # (dato, dónde se llena, ¿está?, ¿obligatorio?)
        ("Nombre del paciente", "Módulo 1", bool(nombre_paciente), True),
        ("Nombre del profesional / estudiante", "Módulo 6", bool(nombre_odonto), True),
        ("N° de documento del paciente", "Módulo 1", bool(num_doc), False),
        ("Consentimiento aceptado", "Módulo 6", acepta_consentimiento, False),
        ("Firma del paciente", "Módulo 6", file_firma_paciente is not None, False),
        ("Firma del profesional", "Módulo 6", file_firma_odonto is not None, False),
    ]
    listo_para_pdf = bool(nombre_paciente and nombre_odonto)
    tarjeta_requisitos(requisitos, listo_para_pdf)

    # Streamlit reciente crea el PDF en el mismo clic (sin recargar); en versiones antiguas se prepara antes.
    diferida = "deferred" in (st.download_button.__doc__ or "").lower()
    st.download_button(
        "📄 GENERAR Y DESCARGAR HISTORIA CLÍNICA (PDF)",
        data=construir_pdf if diferida else (construir_pdf() if listo_para_pdf else b""),
        file_name=f"HC_Odontologica_{(num_doc or 'paciente').strip().replace(' ', '_')}_{fecha_hc.strftime('%Y-%m-%d')}.pdf",
        mime="application/pdf", key="btn_pdf", type="primary", disabled=not listo_para_pdf,
        on_click="ignore" if diferida else None, use_container_width=True)


# ======================= PANEL DE AVANCE (se llena al final) =======================
def avance(*valores):
    llenos = [v.strip() != "" and v != SEL if isinstance(v, str) else bool(v) for v in valores]
    return sum(llenos) / len(llenos)


panel_avance(panel_progreso, [
    ("Datos administrativos", avance(hc_num, eps, nombre_paciente, tipo_doc, num_doc, sexo, direccion, telefono,
                                     estado_civil, ocupacion, tipo_plan, condicion_usuario)),
    ("Anamnesis y antecedentes", avance(motivo, enfermedad_actual, higiene_oral_est, cepillo_dental, seda_dental, enjuagues,
                                        *antecedentes_dict.values())),
    ("Examen estomatológico", avance(obs_examen_fisico, ingesta_carbohidratos, num_comidas)),
    ("Odontograma y diagnóstico", avance(ss.odo_superficies or ss.odo_dientes, diag_principal, cod_principal,
                                         pronostico_gral, plan_areas, desc_plan_tratamiento)),
    ("Evolución", avance(ss.evoluciones)),
    ("Firmas y consentimientos", avance(consentimientos_seleccionados, acepta_consentimiento, nombre_odonto, tarjeta_prof,
                                        file_firma_paciente, file_firma_odonto)),
], listo_pdf=listo_para_pdf)