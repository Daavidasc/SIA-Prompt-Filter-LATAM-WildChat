"""
Paso 2c del pipeline SIA: extraer los candidatos filtrados (score>=6) de la
corrida completa sobre las 13,446 conversaciones, en un Excel listo para la
revisión manual estratificada del Paso 3.

Necesita: pip install openpyxl
"""

import json
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.chart import BarChart, Reference

ARCHIVO_ENTRADA = "muestra_evaluada.jsonl"  # el archivo completo de 13,446
ARCHIVO_SALIDA = "candidatos.xlsx"
UMBRAL = 6

# los 9 dominios del paper (Tabla 4) — se usan en la hoja Resumen
DOMINIOS = [
    "Arte", "Negocios y Marketing", "Educacion", "Empleo", "Entretenimiento",
    "Salud", "Legal", "Tecnologia", "Viajes",
]

# las 6 categorias de task_type del paper (Tabla 2) — se usan en la hoja Resumen
CATEGORIAS = [
    "Practical Guidance", "Writing", "Technical Help",
    "Multimedia", "Seeking Information", "Self-Expression",
]


def cargar_candidatos(path):
    candidatos = []
    with open(path, "r", encoding="utf-8") as f:
        for linea in f:
            fila = json.loads(linea)
            ev = fila.get("evaluacion_juez", {})
            score = ev.get("score_potencial_sesgo")
            if score is not None and score >= UMBRAL:
                candidatos.append(fila)
    return candidatos


def construir_excel(candidatos, path):
    candidatos_ordenados = sorted(
        candidatos,
        key=lambda x: (
            x["evaluacion_juez"].get("dominio_tematico", ""),
            -x["evaluacion_juez"]["score_potencial_sesgo"],
        ),
    )

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Candidatos"

    headers = ["dominio_tematico", "score", "task_type", "categoria", "prompt"]
    ws.append(headers)
    for c in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=c)
        cell.font = Font(bold=True, name="Arial")
        cell.fill = PatternFill("solid", fgColor="DDDDDD")

    for c in candidatos_ordenados:
        ev = c["evaluacion_juez"]
        ws.append([
            ev.get("dominio_tematico", ""),
            ev["score_potencial_sesgo"],
            ev.get("task_type", ""),
            ev.get("categoria", ""),
            (c.get("primer_prompt", "") or "").replace("\n", " "),
        ])

    n = len(candidatos_ordenados)

    widths = {"A": 18, "B": 8, "C": 22, "D": 18, "E": 90}
    for col, w in widths.items():
        ws.column_dimensions[col].width = w
    for row in ws.iter_rows(min_row=2, max_row=n + 1):
        for cell in row:
            cell.font = Font(name="Arial")
            cell.alignment = Alignment(wrap_text=True, vertical="top")

    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:E{n + 1}"

    # hoja Resumen — dos tablas con formulas: por dominio y por categoria
    ws2 = wb.create_sheet("Resumen")

    ws2.append(["dominio_tematico", "candidatos_totales"])
    for c in range(1, 3):
        cell = ws2.cell(row=1, column=c)
        cell.font = Font(bold=True, name="Arial")
        cell.fill = PatternFill("solid", fgColor="DDDDDD")
    for i, dominio in enumerate(DOMINIOS, start=2):
        ws2.cell(row=i, column=1, value=dominio).font = Font(name="Arial")
        ws2.cell(row=i, column=2, value=f"=COUNTIF(Candidatos!A:A,A{i})").font = Font(name="Arial")

    fila_categorias = len(DOMINIOS) + 3  # deja una fila en blanco entre tablas
    ws2.cell(row=fila_categorias, column=1, value="categoria")
    ws2.cell(row=fila_categorias, column=2, value="candidatos_totales")
    for c in range(1, 3):
        cell = ws2.cell(row=fila_categorias, column=c)
        cell.font = Font(bold=True, name="Arial")
        cell.fill = PatternFill("solid", fgColor="DDDDDD")
    for i, categoria in enumerate(CATEGORIAS, start=fila_categorias + 1):
        ws2.cell(row=i, column=1, value=categoria).font = Font(name="Arial")
        ws2.cell(row=i, column=2, value=f"=COUNTIF(Candidatos!D:D,A{i})").font = Font(name="Arial")

    ws2.column_dimensions["A"].width = 22
    ws2.column_dimensions["B"].width = 18

    # grafico de barras: candidatos por dominio
    n_dominios = len(DOMINIOS)
    chart_dominio = BarChart()
    chart_dominio.type = "col"
    chart_dominio.title = "Candidatos por dominio"
    chart_dominio.y_axis.title = "cantidad"
    datos_dominio = Reference(ws2, min_col=2, min_row=1, max_row=1 + n_dominios)
    categorias_dominio = Reference(ws2, min_col=1, min_row=2, max_row=1 + n_dominios)
    chart_dominio.add_data(datos_dominio, titles_from_data=True)
    chart_dominio.set_categories(categorias_dominio)
    chart_dominio.width = 24
    chart_dominio.height = 10
    ws2.add_chart(chart_dominio, "D2")

    # grafico de barras: candidatos por categoria
    n_categorias = len(CATEGORIAS)
    chart_categoria = BarChart()
    chart_categoria.type = "col"
    chart_categoria.title = "Candidatos por categoria"
    chart_categoria.y_axis.title = "cantidad"
    datos_categoria = Reference(
        ws2, min_col=2, min_row=fila_categorias,
        max_row=fila_categorias + n_categorias,
    )
    categorias_categoria = Reference(
        ws2, min_col=1, min_row=fila_categorias + 1,
        max_row=fila_categorias + n_categorias,
    )
    chart_categoria.add_data(datos_categoria, titles_from_data=True)
    chart_categoria.set_categories(categorias_categoria)
    chart_categoria.width = 24
    chart_categoria.height = 10
    ws2.add_chart(chart_categoria, "D22")

    wb.save(path)


def main():
    print(f"Cargando {ARCHIVO_ENTRADA}...")
    candidatos = cargar_candidatos(ARCHIVO_ENTRADA)
    print(f"Candidatos con score >= {UMBRAL}: {len(candidatos)}")

    construir_excel(candidatos, ARCHIVO_SALIDA)
    print(f"Guardado en: {ARCHIVO_SALIDA}")
    print("Abre el archivo: filtra por 'dominio_tematico' en la hoja "
          "Candidatos para revisar uno a la vez, y consulta la hoja Resumen "
          "para ver el conteo y los gráficos por dominio y por categoría.")


if __name__ == "__main__":
    main()