"""Arma el libro de Excel del proyecto.

    python 03_excel.py

El libro NO trae valores pegados: las hojas de analisis se calculan con formulas
de Excel sobre las hojas de datos. Asi el revisor puede cambiar un supuesto y ver
el resultado moverse, que es la diferencia entre un reporte y un modelo.
"""
import os
import sys

import pandas as pd
from openpyxl import Workbook
from openpyxl.chart import BarChart, LineChart, Reference
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(AQUI, "datos")
OUT = os.path.join(AQUI, "Comercio_exterior_CR.xlsx")

AZUL, BLANCO = "1F3864", "FFFFFF"
enc = PatternFill("solid", fgColor=AZUL)
fenc = Font(color=BLANCO, bold=True, size=10)

socio = pd.read_csv(os.path.join(D, "comercio_por_socio.csv"))
prod = pd.read_csv(os.path.join(D, "comercio_por_producto.csv"))
conc = pd.read_csv(os.path.join(D, "hallazgo_concentracion.csv"))

wb = Workbook()
wb.remove(wb.active)


def hoja_datos(nombre, df, ancho):
    ws = wb.create_sheet(nombre)
    ws.append(list(df.columns))
    for fila in df.itertuples(index=False):
        ws.append(list(fila))
    ref = f"A1:{get_column_letter(len(df.columns))}{len(df) + 1}"
    t = Table(displayName=nombre.replace(" ", "_").replace(".", ""), ref=ref)
    t.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)
    ws.add_table(t)
    for i, w in enumerate(ancho, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = "A2"
    return ws


# ----------------------------------------------------------------- datos
hoja_datos("datos_socio", socio, [7, 13, 11, 34, 12, 18])
hoja_datos("datos_producto", prod, [7, 13, 9, 58, 18])
n_soc, n_pro = len(socio) + 1, len(prod) + 1

# ----------------------------------------------------------------- resumen con formulas
ws = wb.create_sheet("Resumen", 0)
ws["A1"] = "COMERCIO EXTERIOR DE COSTA RICA"
ws["A1"].font = Font(size=16, bold=True, color=AZUL)
ws["A2"] = "Fuente: UN COMTRADE · reporter 188 · datos 2010-2024"
ws["A2"].font = Font(size=9, italic=True, color="808080")

ws["A4"] = "Año a consultar"
ws["A4"].font = Font(bold=True)
ws["B4"] = 2024                                  # <- la celda que se cambia
ws["B4"].fill = PatternFill("solid", fgColor="FFF2CC")
ws["B4"].font = Font(bold=True, size=12)
ws["C4"] = "← cambiá este año y todo lo de abajo se recalcula"
ws["C4"].font = Font(size=9, italic=True, color="808080")

filas = [
    ("Exportaciones totales (USD)",
     f'=SUMIFS(datos_socio!F2:F{n_soc},datos_socio!A2:A{n_soc},$B$4,'
     f'datos_socio!B2:B{n_soc},"Exportacion",datos_socio!C2:C{n_soc},0)'),
    ("Importaciones totales (USD)",
     f'=SUMIFS(datos_socio!F2:F{n_soc},datos_socio!A2:A{n_soc},$B$4,'
     f'datos_socio!B2:B{n_soc},"Importacion",datos_socio!C2:C{n_soc},0)'),
    ("Saldo comercial (USD)", "=B6-B7"),
    ("Exportado a Estados Unidos (USD)",
     f'=SUMIFS(datos_socio!F2:F{n_soc},datos_socio!A2:A{n_soc},$B$4,'
     f'datos_socio!B2:B{n_soc},"Exportacion",datos_socio!D2:D{n_soc},"USA")'),
    ("Dependencia de Estados Unidos", "=IFERROR(B9/B6,0)"),
    ("Socios de destino distintos",
     f'=COUNTIFS(datos_socio!A2:A{n_soc},$B$4,datos_socio!B2:B{n_soc},"Exportacion",'
     f'datos_socio!E2:E{n_soc},FALSE)-1'),
    ("Exportado en el capítulo 90 (USD)",
     f'=SUMIFS(datos_producto!E2:E{n_pro},datos_producto!A2:A{n_pro},$B$4,'
     f'datos_producto!B2:B{n_pro},"Exportacion",datos_producto!C2:C{n_pro},90)'),
    ("Peso del capítulo 90", "=IFERROR(B12/B6,0)"),
]
for i, (etq, f) in enumerate(filas, start=6):
    ws.cell(i, 1, etq).font = Font(bold=True)
    c = ws.cell(i, 2, f)
    c.number_format = '0.0%' if "Dependencia" in etq or "Peso" in etq else '#,##0'

ws["A15"] = "Todas las celdas de arriba son fórmulas SUMIFS/COUNTIFS sobre las hojas de datos."
ws["A15"].font = Font(size=9, italic=True, color="808080")
ws.column_dimensions["A"].width = 34
ws.column_dimensions["B"].width = 20
ws.column_dimensions["C"].width = 46

# ----------------------------------------------------------------- concentracion
wsc = wb.create_sheet("Concentracion")
wsc.append(["Año", "Socios", "HHI", "HHI norm.", "Top 1 %", "Top 4 %", "Top 10 %"])
for f in conc.itertuples(index=False):
    wsc.append([int(f.anio), int(f.socios), f.hhi, f.hhi_norm,
                f.top1_pc / 100, f.top4_pc / 100, f.top10_pc / 100])
for c in wsc[1]:
    c.fill, c.font, c.alignment = enc, fenc, Alignment(horizontal="center")
for fila in wsc.iter_rows(min_row=2, min_col=5, max_col=7):
    for c in fila:
        c.number_format = '0.0%'
for i, w in enumerate([8, 9, 10, 11, 10, 10, 10], start=1):
    wsc.column_dimensions[get_column_letter(i)].width = w

g = LineChart()
g.title = "Concentración de los destinos de exportación"
g.y_axis.title = "% de las exportaciones"
g.height, g.width = 9, 18
g.add_data(Reference(wsc, min_col=5, max_col=7, min_row=1, max_row=len(conc) + 1),
           titles_from_data=True)
g.set_categories(Reference(wsc, min_col=1, min_row=2, max_row=len(conc) + 1))
wsc.add_chart(g, "I2")

# ----------------------------------------------------------------- capitulos
cap = pd.read_csv(os.path.join(D, "hallazgo_capitulos.csv"))
wsp = wb.create_sheet("Capitulos")
col_ini, col_fin = cap.columns[2], cap.columns[3]
wsp.append(["Cap.", "Capítulo (HS)", f"{col_ini} (USD)", f"{col_fin} (USD)",
            "Cambio (USD)", "Aporte al crecimiento"])
for f in cap.itertuples(index=False):
    wsp.append([f[0], str(f[1])[:60], f[2], f[3], f[4], f[5] / 100])
for c in wsp[1]:
    c.fill, c.font, c.alignment = enc, fenc, Alignment(horizontal="center", wrap_text=True)
for fila in wsp.iter_rows(min_row=2, min_col=3, max_col=5):
    for c in fila:
        c.number_format = '#,##0'
for fila in wsp.iter_rows(min_row=2, min_col=6, max_col=6):
    for c in fila:
        c.number_format = '0.0%'
for i, w in enumerate([7, 52, 17, 17, 17, 13], start=1):
    wsp.column_dimensions[get_column_letter(i)].width = w

b = BarChart()
b.title = "Qué explica el crecimiento exportador 2010-2024"
b.height, b.width = 9, 18
b.add_data(Reference(wsp, min_col=5, min_row=1, max_row=len(cap) + 1), titles_from_data=True)
b.set_categories(Reference(wsp, min_col=2, min_row=2, max_row=len(cap) + 1))
wsp.add_chart(b, "H2")

wb.save(OUT)
print("Escrito:", OUT)
for h in wb.sheetnames:
    print("  ·", h)
