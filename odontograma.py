"""
ODONTOGRAMA DIBUJADO (sistema FDI)
- Dibuja los dientes con sus 5 superficies y su número.
- Sabe en qué diente y en qué superficie se hizo clic.
- Pinta las convenciones por superficie o por diente completo.
- Calcula el índice O'Leary.
"""

import io
import math

from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------------------
# CONVENCIONES
#   tipo "superficie": pinta solo la superficie tocada
#   tipo "diente":     se dibuja sobre todo el diente
#   icono: texto con color para el botón (formato de Streamlit :color[texto])
# ---------------------------------------------------------------------------
ROJO, AZUL, VERDE, GRIS, MORADO, AMARILLO = "#dc2626", "#2563eb", "#16a34a", "#6b7280", "#9333ea", "#e0a526"

CONVENCIONES = {
    "Borrar (sano)":                     {"tipo": "borrar",     "color": None,     "icono": "○"},
    "Caries":                            {"tipo": "superficie", "color": ROJO,     "icono": ":red[●]"},
    "Amalgama adaptada":                 {"tipo": "superficie", "color": AZUL,     "icono": ":blue[●]"},
    "Resina o ionómero adaptado":        {"tipo": "superficie", "color": VERDE,    "icono": ":green[●]"},
    "Cemento temporal":                  {"tipo": "superficie", "color": GRIS,     "icono": ":gray[●]"},
    "Amalgama desadaptada":              {"tipo": "superficie", "color": AZUL,     "icono": ":blue[◉]", "borde": ROJO},
    "Resina o ionómero desadaptado":     {"tipo": "superficie", "color": VERDE,    "icono": ":green[◉]", "borde": ROJO},
    "Incrustación":                      {"tipo": "superficie", "color": MORADO,   "icono": ":violet[●]"},
    "Placa bacteriana (O'Leary)":        {"tipo": "superficie", "color": AMARILLO, "icono": ":orange[●]"},
    "Endodoncia indicada":               {"tipo": "diente", "color": ROJO,  "figura": "triangulo", "icono": ":red[▲]"},
    "Endodoncia realizada":              {"tipo": "diente", "color": AZUL,  "figura": "triangulo", "icono": ":blue[▲]"},
    "Exodoncia indicada por caries":     {"tipo": "diente", "color": ROJO,  "figura": "x",         "icono": ":red[✕]"},
    "Exodoncia indicada no por caries":  {"tipo": "diente", "color": AZUL,  "figura": "x",         "icono": ":blue[✕]"},
    "Diente perdido por caries":         {"tipo": "diente", "color": ROJO,  "figura": "linea",     "icono": ":red[━]", "ausente": True},
    "Diente perdido no por caries":      {"tipo": "diente", "color": AZUL,  "figura": "linea",     "icono": ":blue[━]", "ausente": True},
    "Sellante adaptado":                 {"tipo": "diente", "color": AZUL,  "figura": "s",         "icono": ":blue[**S**]"},
    "Sellante desadaptado":              {"tipo": "diente", "color": ROJO,  "figura": "s",         "icono": ":red[**S**]"},
    "Diente en erupción":                {"tipo": "diente", "color": AZUL,  "figura": "arriba",    "icono": ":blue[↑]"},
    "Diente sin erupcionar":             {"tipo": "diente", "color": AZUL,  "figura": "izquierda", "icono": ":blue[←]", "ausente": True},
    "Corona adaptada":                   {"tipo": "diente", "color": AZUL,  "figura": "corona",    "icono": ":blue[**O**]"},
    "Corona desadaptada":                {"tipo": "diente", "color": ROJO,  "figura": "corona",    "icono": ":red[**O**]"},
    "Prótesis adaptada":                 {"tipo": "diente", "color": AZUL,  "figura": "igual",     "icono": ":blue[**=**]"},
    "Prótesis desadaptada":              {"tipo": "diente", "color": ROJO,  "figura": "igual",     "icono": ":red[**=**]"},
}

# ---------------------------------------------------------------------------
# DIENTES POR TIPO DE DENTICIÓN (orden de izquierda a derecha en pantalla)
# ---------------------------------------------------------------------------
PERM_SUP = [18, 17, 16, 15, 14, 13, 12, 11, 21, 22, 23, 24, 25, 26, 27, 28]
PERM_INF = [48, 47, 46, 45, 44, 43, 42, 41, 31, 32, 33, 34, 35, 36, 37, 38]
TEMP_SUP = [55, 54, 53, 52, 51, 61, 62, 63, 64, 65]
TEMP_INF = [85, 84, 83, 82, 81, 71, 72, 73, 74, 75]


def filas_denticion(tipo):
    """Filas de dientes a dibujar según el tipo de dentición."""
    if tipo == "Temporal":
        return [TEMP_SUP, TEMP_INF]
    if tipo == "Mixta":
        return [PERM_SUP, TEMP_SUP, TEMP_INF, PERM_INF]
    return [PERM_SUP, PERM_INF]


# ---------------------------------------------------------------------------
# GEOMETRÍA (en píxeles de pantalla; la imagen se dibuja al doble para que se vea nítida)
# ---------------------------------------------------------------------------
ESCALA = 2          # la imagen interna es 2 veces más grande que lo que se muestra
D = 58              # diámetro del diente
PASO = 68           # distancia entre centros de dientes
CENTRO_GAP = 36     # espacio extra entre la mitad derecha e izquierda
FILA_ALTO = 96      # alto de cada fila (diente + número)
MARGEN = 24
ANCHO = MARGEN * 2 + PASO * 16 + CENTRO_GAP


def posiciones(tipo):
    """Devuelve {diente: (cx, cy)} en píxeles de pantalla."""
    pos = {}
    for f, fila in enumerate(filas_denticion(tipo)):
        mitad = len(fila) // 2
        desplazamiento = (8 - mitad) * PASO  # centra las filas de 5 dientes bajo las de 8
        cy = MARGEN + D / 2 + f * FILA_ALTO
        for i, diente in enumerate(fila):
            lado = 0 if i < mitad else 1
            j = i if lado == 0 else i - mitad
            if lado == 0:
                cx = MARGEN + desplazamiento + j * PASO + PASO / 2
            else:
                cx = MARGEN + 8 * PASO + CENTRO_GAP + j * PASO + PASO / 2
            pos[diente] = (cx, cy)
    return pos


def alto_imagen(tipo):
    return int(MARGEN * 2 + FILA_ALTO * len(filas_denticion(tipo)) - (FILA_ALTO - D) + 18)


def nombre_superficie(diente, sup):
    """Traduce la posición en el dibujo (arriba, abajo, izq, der, centro) al nombre clínico."""
    cuadrante = diente // 10
    superior = cuadrante in (1, 2, 5, 6)
    anterior = diente % 10 <= 3
    if sup == "centro":
        return "Incisal" if anterior else "Oclusal"
    if sup == "arriba":
        return "Vestibular" if superior else "Lingual"
    if sup == "abajo":
        return "Palatina" if superior else "Vestibular"
    # Mesial = lado que mira hacia la línea media
    mira_derecha = cuadrante in (1, 4, 5, 8)  # los de la mitad izquierda de la pantalla
    if sup == "derecha":
        return "Mesial" if mira_derecha else "Distal"
    return "Distal" if mira_derecha else "Mesial"


def detectar(tipo, x, y):
    """Dado un clic (en píxeles de pantalla) devuelve (diente, superficie) o (None, None)."""
    R, r = D / 2, D * 0.22
    for diente, (cx, cy) in posiciones(tipo).items():
        dx, dy = x - cx, y - cy
        dist = math.hypot(dx, dy)
        if dist <= R + 3:
            if dist <= r:
                return diente, "centro"
            if abs(dy) >= abs(dx):
                return diente, "arriba" if dy < 0 else "abajo"
            return diente, "derecha" if dx > 0 else "izquierda"
    return None, None


# ---------------------------------------------------------------------------
# DIBUJO
# ---------------------------------------------------------------------------
def _fuente(tamano, negrita=False):
    nombres = (["arialbd.ttf", "Arial Bold.ttf", "DejaVuSans-Bold.ttf"] if negrita
            else ["arial.ttf", "Arial.ttf", "DejaVuSans.ttf"])
    for n in nombres:
        try:
            return ImageFont.truetype(n, tamano)
        except OSError:
            pass
    try:
        return ImageFont.load_default(size=tamano)
    except TypeError:
        return ImageFont.load_default()


def _sector(cx, cy, R, r, a1, a2, pasos=24):
    """Polígono de un sector del anillo entre los ángulos a1 y a2 (grados)."""
    externo = [(cx + R * math.cos(math.radians(a1 + (a2 - a1) * i / pasos)),
                cy + R * math.sin(math.radians(a1 + (a2 - a1) * i / pasos))) for i in range(pasos + 1)]
    interno = [(cx + r * math.cos(math.radians(a2 - (a2 - a1) * i / pasos)),
                cy + r * math.sin(math.radians(a2 - (a2 - a1) * i / pasos))) for i in range(pasos + 1)]
    return externo + interno


ANGULOS = {"arriba": (-135, -45), "derecha": (-45, 45), "abajo": (45, 135), "izquierda": (135, 225)}


def dibujar(tipo, superficies, dientes):
    """
    superficies: {"17-arriba": "Caries", ...}
    dientes:     {"17": "Endodoncia indicada", ...}
    Devuelve una imagen PIL.
    """
    S = ESCALA
    img = Image.new("RGB", (ANCHO * S, alto_imagen(tipo) * S), "white")
    d = ImageDraw.Draw(img)
    fuente_num = _fuente(13 * S)
    fuente_s = _fuente(int(D * 0.95) * S, negrita=True)
    trazo = "#4b5563"
    R, r = D / 2 * S, D * 0.22 * S

    for diente, (px, py) in posiciones(tipo).items():
        cx, cy = px * S, py * S

        # 1) Superficies pintadas
        for sup in ("arriba", "derecha", "abajo", "izquierda", "centro"):
            conv = superficies.get(f"{diente}-{sup}")
            if not conv:
                continue
            info = CONVENCIONES[conv]
            if sup == "centro":
                forma = [(cx - r, cy - r), (cx + r, cy + r)]
                d.ellipse(forma, fill=info["color"])
                if info.get("borde"):
                    d.ellipse(forma, outline=info["borde"], width=3 * S)
            else:
                poli = _sector(cx, cy, R, r, *ANGULOS[sup])
                d.polygon(poli, fill=info["color"])
                if info.get("borde"):
                    d.line(poli + [poli[0]], fill=info["borde"], width=3 * S, joint="curve")

        # 2) Contorno del diente: círculo externo, interno y las 4 diagonales
        d.ellipse([(cx - R, cy - R), (cx + R, cy + R)], outline=trazo, width=2 * S)
        d.ellipse([(cx - r, cy - r), (cx + r, cy + r)], outline=trazo, width=2 * S)
        for ang in (45, 135, 225, 315):
            c, s = math.cos(math.radians(ang)), math.sin(math.radians(ang))
            d.line([(cx + r * c, cy + r * s), (cx + R * c, cy + R * s)], fill=trazo, width=2 * S)

        # 3) Número del diente
        d.text((cx, cy + R + 14 * S), str(diente), fill="#111827", font=fuente_num, anchor="mm")

        # 4) Marca de diente completo
        conv = dientes.get(str(diente))
        if conv:
            info = CONVENCIONES[conv]
            col, fig, g = info["color"], info["figura"], 4 * S
            if fig == "triangulo":
                d.polygon([(cx, cy - R * 0.85), (cx - R * 0.8, cy + R * 0.6), (cx + R * 0.8, cy + R * 0.6)], fill=col)
            elif fig == "x":
                d.line([(cx - R, cy - R), (cx + R, cy + R)], fill=col, width=g)
                d.line([(cx + R, cy - R), (cx - R, cy + R)], fill=col, width=g)
            elif fig == "linea":
                d.line([(cx - R - 3 * S, cy), (cx + R + 3 * S, cy)], fill=col, width=g)
            elif fig == "s":
                d.text((cx, cy), "S", fill=col, font=fuente_s, anchor="mm")
            elif fig == "corona":
                d.ellipse([(cx - R - 2 * S, cy - R - 2 * S), (cx + R + 2 * S, cy + R + 2 * S)], outline=col, width=5 * S)
            elif fig == "igual":
                d.line([(cx - R - 3 * S, cy - 7 * S), (cx + R + 3 * S, cy - 7 * S)], fill=col, width=g)
                d.line([(cx - R - 3 * S, cy + 7 * S), (cx + R + 3 * S, cy + 7 * S)], fill=col, width=g)
            elif fig == "arriba":
                d.line([(cx, cy + R), (cx, cy - R)], fill=col, width=g)
                d.polygon([(cx, cy - R - 4 * S), (cx - 9 * S, cy - R + 11 * S), (cx + 9 * S, cy - R + 11 * S)], fill=col)
            elif fig == "izquierda":
                d.line([(cx + R, cy), (cx - R, cy)], fill=col, width=g)
                d.polygon([(cx - R - 4 * S, cy), (cx - R + 11 * S, cy - 9 * S), (cx - R + 11 * S, cy + 9 * S)], fill=col)
    return img


def a_png(img):
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


# ---------------------------------------------------------------------------
# ÍNDICE O'LEARY
# ---------------------------------------------------------------------------
def indice_oleary(tipo, superficies, dientes):
    """O'Leary: superficies con placa ÷ (dientes presentes × 4) × 100.
    Se cuentan 4 superficies por diente (vestibular, lingual/palatina, mesial, distal).
    Los dientes perdidos o sin erupcionar no se cuentan."""
    presentes = [t for t in posiciones(tipo)
                if not CONVENCIONES.get(dientes.get(str(t), ""), {}).get("ausente")]
    total = len(presentes) * 4
    tenidas = sum(1 for t in presentes for sup in ("arriba", "abajo", "izquierda", "derecha")
                if superficies.get(f"{t}-{sup}") == "Placa bacteriana (O'Leary)")
    porcentaje = round(tenidas / total * 100) if total else 0
    return total, tenidas, porcentaje


def tabla_hallazgos(superficies, dientes):
    """Lista de filas para la tabla y el PDF."""
    filas = []
    for clave, conv in superficies.items():
        diente, sup = clave.split("-")
        filas.append({"Diente": diente, "Hallazgo": conv,
                    "Superficies": nombre_superficie(int(diente), sup), "Observación": ""})
    for diente, conv in dientes.items():
        filas.append({"Diente": diente, "Hallazgo": conv, "Superficies": "Pieza completa", "Observación": ""})
    return sorted(filas, key=lambda f: (int(f["Diente"]), f["Superficies"]))