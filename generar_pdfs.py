#!/usr/bin/env python3
"""
Genera los documentos PDF de la entrega a partir de ejecuciones REALES del sistema:

  docs/Pruebas_Sistema_Rutas.pdf  -> documento con las pruebas realizadas
  docs/Entrega_Actividad2.pdf     -> documento con los enlaces (repositorio y video)

Uso:
  python generar_pdfs.py

Los enlaces e integrantes predeterminados corresponden a la entrega de Actividad 2.
Se pueden cambiar mediante --repo, --video y --integrantes.

Requiere: pip install reportlab matplotlib
"""
from __future__ import annotations

import argparse
import datetime as dt
import io
import os
import subprocess
import sys
import unittest

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph, Preformatted, SimpleDocTemplate,
                                Spacer, Table, TableStyle)

RAIZ = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, RAIZ)

from motor.mapa import dibujar  # noqa: E402
from motor.sistema import EstacionNoEncontrada, SistemaRutas  # noqa: E402

DOCS = os.path.join(RAIZ, "docs")
MARGEN = 2.54 * cm
ANCHO_UTIL = A4[0] - 2 * MARGEN - 12


def fuente_academica():
    """Usa Times New Roman instalada; Times estándar permite generar en otros sistemas."""
    directorio = os.path.join(os.environ.get("WINDIR", "C:/Windows"), "Fonts")
    archivos = {"Academica": "times.ttf", "Academica-Bold": "timesbd.ttf",
                "Academica-Italic": "timesi.ttf", "Academica-BoldItalic": "timesbi.ttf"}
    if all(os.path.isfile(os.path.join(directorio, a)) for a in archivos.values()):
        for nombre, archivo in archivos.items():
            pdfmetrics.registerFont(TTFont(nombre, os.path.join(directorio, archivo)))
        pdfmetrics.registerFontFamily("Academica", normal="Academica", bold="Academica-Bold",
                                      italic="Academica-Italic", boldItalic="Academica-BoldItalic")
        return "Academica", "Academica-Bold"
    return "Times-Roman", "Times-Bold"


FUENTE, NEGRITA = fuente_academica()

# ---------------------------------------------------------------- estilos
base = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=base["Heading1"], fontName=NEGRITA, fontSize=12,
                    leading=13.9, alignment=TA_CENTER, spaceBefore=12, spaceAfter=12,
                    textColor=colors.black)
H2 = ParagraphStyle("H2", parent=H1)
TXT = ParagraphStyle("TXT", parent=base["BodyText"], fontName=FUENTE, fontSize=12,
                     leading=13.9, firstLineIndent=1.25 * cm, spaceBefore=0, spaceAfter=8,
                     textColor=colors.black)
PEQ = ParagraphStyle("PEQ", parent=TXT, fontSize=10, leading=11.6,
                     firstLineIndent=0, spaceAfter=0)
CAB = ParagraphStyle("CAB", parent=PEQ, fontName=NEGRITA)
CEN = ParagraphStyle("CEN", parent=TXT, alignment=TA_CENTER, firstLineIndent=0)
TIT = ParagraphStyle("TIT", parent=CEN, fontName=NEGRITA)
CODE = ParagraphStyle("CODE", fontName="Courier", fontSize=8, leading=9.7,
                      spaceBefore=4, spaceAfter=8)


def enlace(valor):
    from xml.sax.saxutils import escape
    v = escape(valor, {chr(39): "&apos;"})
    if not valor.startswith("https://"):
        return v
    visible = v.replace("https://github.com/", "https://github.com/<br/>")
    visible = visible.replace("/blob/main/", "/<br/>blob/main/")
    return f"<link href='{v}'>{visible}</link>"


def tabla(filas, anchos, cabecera=True):
    total = sum(anchos)
    anchos = [a * min(1, ANCHO_UTIL / total) for a in anchos]
    t = Table([[Paragraph(str(c), CAB if i == 0 and cabecera else PEQ) for c in f] for i, f in enumerate(filas)], colWidths=anchos, repeatRows=1)
    estilo = [("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#bbbbbb")),
              ("VALIGN", (0, 0), (-1, -1), "TOP"),
              ("TOPPADDING", (0, 0), (-1, -1), 2),
              ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]
    if cabecera:
        estilo += [("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eeeeee")),
                   ("TEXTCOLOR", (0, 0), (-1, 0), colors.black)]
    t.setStyle(TableStyle(estilo))
    return t


def ejecutar(args):
    """Ejecuta main.py como lo haría el usuario y devuelve la salida de consola."""
    r = subprocess.run([sys.executable, "main.py", *args], cwd=RAIZ, capture_output=True,
                       text=True, encoding="utf-8", env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    return (r.stdout + r.stderr).rstrip()


def consola(cmd_args):
    comando = "python main.py " + " ".join(f'"{a}"' if " " in a else a for a in cmd_args)
    texto = "$ " + comando + "\n" + ejecutar(cmd_args)
    return Preformatted(envolver(texto), CODE)


def envolver(texto, ancho=90):
    import textwrap
    lineas = []
    for l in texto.splitlines():
        sangria = " " * (len(l) - len(l.lstrip()) + 3)
        lineas += textwrap.wrap(l, ancho, subsequent_indent=sangria, break_long_words=True) or [""]
    return "\n".join(lineas)


def pie(canvas, doc):
    canvas.saveState()
    canvas.setFont(FUENTE, 12)
    canvas.setFillColor(colors.black)
    canvas.drawRightString(A4[0] - MARGEN, A4[1] - 1.27 * cm, str(doc.page))
    canvas.restoreState()


def portada(titulo, subtitulo, integrantes, extra=()):
    tipo = "Documento de pruebas" if extra else "Documento de entrega"
    h = [Paragraph("CORPORACIÓN UNIVERSITARIA IBEROAMERICANA", TIT),
         Paragraph("INTELIGENCIA ARTIFICIAL", TIT),
         Paragraph("Actividad 2<br/>Búsqueda y sistemas basados en reglas<br/>" + tipo, TIT),
         Spacer(1, 2.25 * cm), Paragraph("Trabajo de:", TIT)]
    h += [Paragraph(n.upper(), TIT) for n in integrantes]
    h += [Spacer(1, 5.15 * cm), Paragraph("Docente:", TIT),
          Paragraph("SANDRA ISABEL RODRIGUEZ BAUTISTA", TIT), Spacer(1, 5.0 * cm),
          Paragraph("Fecha de entrega:", TIT)]
    fecha = dt.date.today()
    dias = ("Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo")
    meses = ("enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
             "septiembre", "octubre", "noviembre", "diciembre")
    h += [Paragraph(f"{dias[fecha.weekday()]}, {fecha.day} de {meses[fecha.month - 1]} de {fecha.year}", TIT), PageBreak()]
    if extra:
        h.append(Paragraph("Enlaces del proyecto", H2))
        for e in extra:
            etiqueta, valor = e.split(": ", 1)
            h.append(Paragraph(etiqueta + ": " + enlace(valor), PEQ))
        h.append(Spacer(1, 12))
    return h


# ---------------------------------------------------------------- pruebas
def correr_unittest():
    suite = unittest.defaultTestLoader.discover(os.path.join(RAIZ, "tests"))
    salida = io.StringIO()
    res = unittest.TextTestRunner(stream=salida, verbosity=2).run(suite)
    return res, salida.getvalue()


def informe_pruebas(integrantes, repo, video):
    s = SistemaRutas()
    kb = s.kb
    h = portada("Sistema inteligente de rutas<br/>Metro de Medellín",
                "Actividad 2 - Búsqueda y sistemas basados en reglas<br/>Documento de pruebas",
                integrantes, [f"Repositorio: {repo}", f"Video: {video}"])

    # 1. Descripción
    h += [Paragraph("1. Descripción del sistema", H1), Paragraph(
        "El sistema responde a la pregunta <i>¿cuál es la mejor ruta para ir de la estación A a la "
        "estación B?</i> combinando dos técnicas de IA: (1) una <b>base de conocimiento</b> escrita en "
        "reglas lógicas (sintaxis tipo Prolog/Datalog) que un <b>motor de inferencia por encadenamiento "
        "hacia adelante</b> procesa para deducir conexiones, transbordos, estaciones disponibles y "
        "alcanzabilidad; y (2) una <b>búsqueda heurística A*</b> que recorre únicamente los movimientos "
        "que las reglas declaran válidos.", TXT), Spacer(1, 6)]
    h.append(tabla([
        ["Elemento", "Valor"],
        ["Líneas", str(len(s.lineas))],
        ["Estaciones", str(len(s.nombres))],
        ["Reglas lógicas", str(len(kb.reglas))],
        ["Hechos base (declarados)", str(kb.hechos_base)],
        ["Hechos inferidos por el motor", str(kb.hechos_inferidos)],
        ["Iteraciones hasta el punto fijo", str(kb.iteraciones)],
        ["Estaciones de transbordo inferidas", ", ".join(s.nombre(e) for e in s.estaciones_transbordo())],
        ["Penalización por transbordo", f"{s.penalizacion:g} minutos"],
    ], [6 * cm, 10.5 * cm]))

    h += [Paragraph("1.1 Reglas de la base de conocimiento", H2)]
    h.append(Preformatted(envolver("\n".join(str(r) for r in kb.reglas)), CODE))
    h += [Spacer(1, 6), Paragraph(
        "<b>Estado</b> = (estación, línea actual). <b>Costo</b> = minutos del tramo + penalización "
        "si se cambia de línea. <b>Heurística</b> h(n) = distancia en línea recta (fórmula de "
        "haversine) hasta el destino ÷ velocidad máxima observada en la red "
        f"({s.buscador.vmax * 60:.1f} km/h). Como ningún tramo supera esa velocidad, h(n) nunca "
        "sobreestima el costo restante bajo los costos positivos y la penalización no negativa de este modelo. "
        "La comprobación se limita a los escenarios evaluados; no valida parámetros arbitrarios.", TXT)]
    h.append(PageBreak())

    # 2. Casos de prueba
    h.append(Paragraph("2. Casos de prueba funcionales", H1))
    casos = []

    def caso(id_, nombre, esperado, obtenido, ok):
        casos.append([id_, nombre, esperado, obtenido, "APROBADA" if ok else "FALLIDA"])

    r1 = s.buscar("La Estrella", "Arví")
    caso("P1", "La Estrella -> Arví con A*",
         "Ruta encontrada, óptima, igual a Costo Uniforme",
         f"{r1.costo:g} min, {r1.paradas} paradas, {r1.transbordos} transbordos (A, K, L)",
         r1.encontrada and r1.costo == s.buscar("la_estrella", "arvi", "ucs").costo)
    r2 = s.buscar("Niquía", "San Javier")
    caso("P2", "Niquía -> San Javier", "Línea A hasta San Antonio y Línea B",
         f"{r2.costo:g} min, líneas: " + ", ".join(dict.fromkeys(p.linea for p in r2.pasos)),
         r2.encontrada and r2.transbordos == 1)
    r3 = s.buscar("Niquía", "Poblado")
    caso("P3", "Niquía -> Poblado (misma línea)", "0 transbordos",
         f"{r3.costo:g} min, {r3.transbordos} transbordos", r3.transbordos == 0)
    s_cerr = SistemaRutas(cerradas=["san_antonio"])
    r4 = s_cerr.buscar("Niquía", "San Javier")
    caso("P4", "Niquía -> San Javier con San Antonio cerrada",
         "Ruta alterna por Metroplús (Hospital -> Cisneros)",
         f"Normal {r2.costo:g} min; con cierre {r4.costo:g} min por "
         + ", ".join(s.nombre(e) for e in r4.estaciones if e in s.estaciones_transbordo()),
         r4.encontrada and "san_antonio" not in r4.estaciones)
    r5 = s_cerr.buscar("Niquía", "Oriente")
    caso("P5", "Niquía -> Oriente con San Antonio cerrada",
         "Sin ruta: la regla R6 excluye San Antonio y el tranvía queda aislado",
         "Sin ruta" if not r5.encontrada else "Encontró ruta", not r5.encontrada)
    v = s.buscar("Parque Berrío", "La Estrella", "greedy")
    a6 = s.buscar("Parque Berrío", "La Estrella")
    caso("P6", "Parque Berrío -> La Estrella: Voraz vs A*",
         "Voraz no garantiza el óptimo; A* sí",
         f"Voraz {v.costo:g} min ({v.transbordos} transb.); A* {a6.costo:g} min ({a6.transbordos} transb.)",
         v.costo > a6.costo)
    q = kb.consultar("transbordo(X)")
    caso("P7", "Consulta lógica transbordo(X)", "9 estaciones inferidas",
         f"{len(q)} resultados", len(q) == 9)
    caso("P8", "Consulta alcanzable(niquia, arvi)", "true",
         str(kb.es_verdad("alcanzable(niquia, arvi)")).lower(),
         kb.es_verdad("alcanzable(niquia, arvi)"))
    try:
        s.resolver("Parque")
        ok9, obt9 = False, "No lanzó error"
    except EstacionNoEncontrada as e:
        ok9, obt9 = bool(e.sugerencias), f"Error con {len(e.sugerencias)} sugerencias"
    caso("P9", "Estación ambigua 'Parque'", "Error controlado con sugerencias", obt9, ok9)
    r10 = s.buscar("itagui", "santo domingo savio")
    caso("P10", "Nombres sin tildes ni mayúsculas (itagui -> santo domingo savio)", "Se resuelven los nombres",
         f"{s.nombre(r10.estaciones[0])} -> {s.nombre(r10.estaciones[-1])}", r10.encontrada)

    h.append(tabla([["ID", "Caso", "Resultado esperado", "Resultado obtenido", "Estado"]] + casos,
                   [1.2 * cm, 3.9 * cm, 4.1 * cm, 4.6 * cm, 3 * cm]))
    aprob = sum(1 for c in casos if c[-1] == "APROBADA")
    h += [Spacer(1, 6), Paragraph(f"<b>{aprob} de {len(casos)} casos aprobados.</b>", TXT)]

    # 3. Evidencia de consola
    h += [PageBreak(), Paragraph("3. Evidencia de ejecución (salida real de consola)", H1)]
    h += [Paragraph("P1 - Ruta de La Estrella a Arví, comparando algoritmos", H2),
          consola(["--origen", "La Estrella", "--destino", "Arví", "--comparar"])]
    mapa = dibujar(s, r1, os.path.join(DOCS, "mapa_ruta.png"), f"La Estrella -> Arví (A*, {r1.costo:g} min)")
    h += [Spacer(1, 6), Image(mapa, width=12 * cm, height=13.4 * cm)]
    h += [PageBreak(), Paragraph("P2 - Niquía -> San Javier", H2),
          consola(["-o", "Niquía", "-d", "San Javier"])]
    h += [Paragraph("P4 / P5 - Estación cerrada (San Antonio)", H2),
          consola(["-o", "Niquía", "-d", "San Javier", "--cerrar", "san_antonio",
                   "-q", "alcanzable(niquia, oriente)"])]
    h += [Paragraph("P6 - Voraz contra A*", H2),
          consola(["-o", "Parque Berrío", "-d", "La Estrella", "-a", "greedy", "--comparar"])]
    h += [Paragraph("P7 / P8 - Consultas a la base de conocimiento", H2),
          consola(["-q", "transbordo(X)", "-q", "conecta_lineas(linea_a, L)",
                   "-q", "alcanzable(niquia, arvi)"])]
    h += [Paragraph("P9 - Estación ambigua", H2), consola(["-o", "Parque", "-d", "Poblado"])]

    # 4. Comparación de algoritmos
    h += [PageBreak(), Paragraph("4. Comparación de estrategias de búsqueda", H1), Paragraph(
        "Se ejecutaron los cuatro algoritmos sobre los mismos pares origen-destino. <b>A*</b> y "
        "<b>Costo uniforme</b> obtienen el mismo menor tiempo en los pares evaluados. A* utiliza "
        "la heurística. <b>Amplitud (BFS)</b> minimiza el número de paradas, no el tiempo, y "
        "<b>Voraz</b> es rápido pero no garantiza la ruta óptima.", TXT), Spacer(1, 6)]
    pares = [("La Estrella", "Arví"), ("Niquía", "San Javier"), ("El Progreso", "Villa Sierra"),
             ("Universidad de Medellín", "La Aurora"), ("Parque Berrío", "La Estrella"),
             ("Vallejuelos", "Universidad"), ("Parque de Aranjuez", "Trece de Noviembre")]
    filas = [["Origen -> Destino", "Algoritmo", "Costo (min)", "Paradas", "Transb.", "Nodos expandidos"]]
    resumen = {a: [0, 0, 0] for a in ("A*", "Costo uniforme", "Amplitud (BFS)", "Voraz (greedy)")}
    for o, d in pares:
        optimo = s.buscar(o, d, "ucs").costo
        for r in s.comparar(o, d):
            filas.append([f"{o} -> {d}", r.algoritmo, f"{r.costo:g}", r.paradas, r.transbordos,
                          r.nodos_expandidos])
            resumen[r.algoritmo][0] += r.nodos_expandidos
            resumen[r.algoritmo][1] += 1 if abs(r.costo - optimo) < 1e-9 else 0
            resumen[r.algoritmo][2] += r.costo
    comparacion = tabla(filas, [4.6 * cm, 3.2 * cm, 2.2 * cm, 1.8 * cm, 1.9 * cm, 3 * cm])
    comparacion.setStyle(TableStyle([("NOSPLIT", (0, i), (-1, i + 3))
                                    for i in range(1, len(filas), 4)]))
    h.append(comparacion)
    h += [KeepTogether([Paragraph("Resumen", H2), tabla(
        [["Algoritmo", "Nodos expandidos (total)", "Rutas óptimas", "Tiempo total (min)"]] +
        [[a, v[0], f"{v[1]} de {len(pares)}", f"{v[2]:g}"] for a, v in resumen.items()],
        [4.5 * cm, 4.5 * cm, 3.5 * cm, 4 * cm])])]

    # 5. Pruebas unitarias
    res, texto = correr_unittest()
    h += [Spacer(1, 16), Paragraph("5. Pruebas unitarias automatizadas", H1), Paragraph(
        f"Comando: <font face='Courier'>python -m unittest discover -s tests -v</font>. "
        f"Resultado: <b>{res.testsRun} pruebas ejecutadas, {len(res.failures)} fallos, "
        f"{len(res.errors)} errores.</b>", TXT), Spacer(1, 4), Preformatted(envolver(texto.strip()), CODE)]

    # 6. Conclusiones
    h += [Paragraph("6. Conclusiones", H1)]
    for c in [
        "Separar el conocimiento (archivo .kb) del código permite modificar la red, los tiempos o "
        "cerrar estaciones sin reprogramar: el motor de inferencia deduce de nuevo los movimientos válidos.",
        "Las reglas recursivas (alcanzable) y con negación (disponible) muestran cómo un sistema basado "
        "en reglas puede razonar sobre conectividad y restricciones antes de ejecutar la búsqueda.",
        "En los siete pares evaluados, A* obtuvo el mismo costo óptimo que Costo Uniforme, "
        "expandiendo igual o menos nodos.",
        "BFS y la búsqueda voraz son útiles como comparación: la primera minimiza paradas y la "
        "segunda es rápida, pero ninguna garantiza el menor tiempo total.",
        "Limitación: es un modelo simplificado; los tiempos y coordenadas son aproximados y no se "
        "modelan frecuencias ni horarios reales, ni la Línea 2 de Metroplús o las rutas alimentadoras.",
    ]:
        h.append(Paragraph("• " + c, TXT))

    ruta = os.path.join(DOCS, "Pruebas_Sistema_Rutas.pdf")
    SimpleDocTemplate(ruta, pagesize=A4, leftMargin=MARGEN, rightMargin=MARGEN,
                      topMargin=MARGEN, bottomMargin=MARGEN,
                      title="Pruebas - Sistema inteligente de rutas Metro de Medellín").build(
        h, onFirstPage=pie, onLaterPages=pie)
    return ruta, aprob, len(casos), res


def documento_entrega(integrantes, repo, video):
    h = portada("Actividad 2<br/>Búsqueda y sistemas basados en reglas",
                "Mejor ruta entre dos estaciones del sistema de transporte masivo (Metro de Medellín)",
                integrantes)
    h += [Paragraph("Enlaces de la entrega", H1), tabla([
        ["Elemento", "Enlace"],
        ["Repositorio Git (código fuente, instrucciones y PDF de pruebas)", enlace(repo)],
        ["Documento de pruebas", enlace(repo.rstrip('/') + "/blob/main/docs/Pruebas_Sistema_Rutas.pdf")],
        ["Video explicativo (máx. 10 min)", enlace(video)],
    ], [7 * cm, 9.5 * cm]), Spacer(1, 12),
        Paragraph("Instrucciones de ejecución", H2),
        Preformatted("Desde la carpeta del proyecto:\n"
                     "python main.py --origen \"La Estrella\" --destino \"Arví\" --comparar\n"
                     "python -m unittest discover -s tests -v", CODE),
        Spacer(1, 10), Paragraph(
            "El repositorio es público e incluye el código y los documentos académicos. "
            "El video final de 8 minutos y 4 segundos está disponible en YouTube mediante el enlace de esta tabla. "
            "El historial original de Geraldine Ríos se conserva; "
            "la preparación de documentación y entrega se registra por separado. "
            "La invitación formal a Sandra Isabel Rodriguez Bautista como colaboradora sigue pendiente: no se dispone de su "
            "usuario de GitHub. La visibilidad pública permite consultar los archivos por enlace, pero no "
            "equivale a una invitación como colaboradora.", TXT)]
    ruta = os.path.join(DOCS, "Entrega_Actividad2.pdf")
    SimpleDocTemplate(ruta, pagesize=A4, leftMargin=MARGEN, rightMargin=MARGEN,
                      topMargin=MARGEN, bottomMargin=MARGEN, title="Entrega Actividad 2").build(
        h, onFirstPage=pie, onLaterPages=pie)
    return ruta


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--repo", default="https://github.com/Dumo04/actividad2-rutas-metro-medellin")
    p.add_argument("--video", default="https://www.youtube.com/watch?v=CBGlb2Fn-Ms")
    p.add_argument("--integrantes", nargs="+",
                   default=["Santiago Duque Mora", "Geraldine Ríos"])
    a = p.parse_args()
    os.makedirs(DOCS, exist_ok=True)
    ruta, aprob, total, res = informe_pruebas(a.integrantes, a.repo, a.video)
    print(f"Generado: {ruta}  ({aprob}/{total} casos aprobados, {res.testsRun} pruebas unitarias OK="
          f"{res.wasSuccessful()})")
    print(f"Generado: {documento_entrega(a.integrantes, a.repo, a.video)}")


if __name__ == "__main__":
    main()
