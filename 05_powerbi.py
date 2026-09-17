"""Prepara el modelo dimensional para Power BI.

    python 05_powerbi.py

Power BI Desktop no se puede automatizar desde Python: el .pbix es un formato
cerrado. Lo que si se puede -y es lo que de verdad decide si un tablero sirve-
es dejar el modelo bien armado: tablas limpias, una dimension de calendario, y
las medidas DAX escritas.

Genera:
  powerbi/dim_socio.csv, dim_capitulo.csv, dim_anio.csv, hechos.csv
  powerbi/medidas.dax
"""
import os
import sys

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(AQUI, "datos")
PBI = os.path.join(AQUI, "powerbi")
os.makedirs(PBI, exist_ok=True)

socio = pd.read_csv(os.path.join(D, "comercio_por_socio.csv"))
prod = pd.read_csv(os.path.join(D, "comercio_por_producto.csv"))

# El codigo 0 es el total mundial, no un socio: se saca del hecho o se contaria
# dos veces. Los agregados regionales, lo mismo.
paises = socio[(socio.socio_cod != 0) & (~socio.es_agregado)].copy()

dim_socio = (paises[["socio_cod", "socio"]].drop_duplicates()
             .sort_values("socio").reset_index(drop=True))
dim_socio.to_csv(os.path.join(PBI, "dim_socio.csv"), index=False, encoding="utf-8-sig")

dim_cap = (prod[["cap_cod", "capitulo"]].drop_duplicates()
           .sort_values("cap_cod").reset_index(drop=True))
dim_cap.to_csv(os.path.join(PBI, "dim_capitulo.csv"), index=False, encoding="utf-8-sig")

anios = sorted(set(paises.anio) | set(prod.anio))
pd.DataFrame({"anio": anios,
              "decada": [f"{a//10*10}s" for a in anios],
              "fecha": [f"{a}-12-31" for a in anios]}
             ).to_csv(os.path.join(PBI, "dim_anio.csv"), index=False, encoding="utf-8-sig")

# Un solo hecho con las dos granularidades marcadas: Power BI filtra por 'grano'.
h1 = paises.assign(grano="socio", cap_cod=pd.NA)[
    ["anio", "flujo", "grano", "socio_cod", "cap_cod", "valor_usd"]]
h2 = prod.assign(grano="capitulo", socio_cod=pd.NA)[
    ["anio", "flujo", "grano", "socio_cod", "cap_cod", "valor_usd"]]
hechos = pd.concat([h1, h2], ignore_index=True)
hechos.to_csv(os.path.join(PBI, "hechos.csv"), index=False, encoding="utf-8-sig")

DAX = r"""// Medidas DAX — pegar una por una en Power BI (Modelado > Nueva medida)

Valor = SUM(hechos[valor_usd])

Exportaciones =
CALCULATE([Valor], hechos[flujo] = "Exportacion")

Importaciones =
CALCULATE([Valor], hechos[flujo] = "Importacion")

Saldo comercial = [Exportaciones] - [Importaciones]

// Total del anio ignorando el filtro de socio: es el denominador de la cuota.
Exportaciones del anio =
CALCULATE([Exportaciones], ALL(dim_socio), ALL(dim_capitulo))

Cuota del destino =
DIVIDE([Exportaciones], [Exportaciones del anio])

// Concentracion: suma de los cuadrados de las cuotas de cada socio.
// 0 = perfectamente disperso, 1 = un solo destino.
HHI =
VAR Total = [Exportaciones del anio]
RETURN
SUMX(
    VALUES(dim_socio[socio_cod]),
    VAR Cuota = DIVIDE(CALCULATE([Exportaciones]), Total)
    RETURN Cuota * Cuota
)

// Cuanto pesan los N destinos mas grandes.
Top 4 destinos % =
VAR Total = [Exportaciones del anio]
VAR Top =
    TOPN(4, VALUES(dim_socio[socio_cod]), CALCULATE([Exportaciones]), DESC)
RETURN
DIVIDE(SUMX(Top, CALCULATE([Exportaciones])), Total)

Dependencia de EEUU =
DIVIDE(
    CALCULATE([Exportaciones], dim_socio[socio] = "USA"),
    [Exportaciones del anio]
)

// Variacion contra el anio anterior, por posicion en dim_anio.
Exportaciones anio anterior =
VAR A = SELECTEDVALUE(dim_anio[anio])
RETURN CALCULATE([Exportaciones], ALL(dim_anio), dim_anio[anio] = A - 1)

Crecimiento % =
DIVIDE([Exportaciones] - [Exportaciones anio anterior],
       [Exportaciones anio anterior])
"""
open(os.path.join(PBI, "medidas.dax"), "w", encoding="utf-8").write(DAX)

print("Modelo para Power BI en powerbi/")
for n in ("dim_socio", "dim_capitulo", "dim_anio", "hechos"):
    print(f"  {n + '.csv':20} {len(pd.read_csv(os.path.join(PBI, n + '.csv'))):>6} filas")
print("  medidas.dax          10 medidas")
