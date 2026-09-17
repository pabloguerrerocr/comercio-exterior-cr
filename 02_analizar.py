"""Calcula los hallazgos del comercio exterior de Costa Rica.

    python 02_analizar.py

Mide tres cosas que un cuadro de totales no muestra:
  · concentracion de destinos (Herfindahl y top-N)
  · como cambio la dependencia de Estados Unidos
  · que capitulos explican el crecimiento de las exportaciones
"""
import os
import sys

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(AQUI, "datos")

s = pd.read_csv(os.path.join(D, "comercio_por_socio.csv"))
p = pd.read_csv(os.path.join(D, "comercio_por_producto.csv"))

# El codigo 0 es "el mundo": es el total, no un socio. Los agregados regionales
# tampoco son socios; sumarlos junto a los paises contaria dos veces.
paises = s[(s.socio_cod != 0) & (~s.es_agregado)]
mundo = s[s.socio_cod == 0].set_index(["flujo", "anio"]).valor_usd


def concentracion(g):
    """Herfindahl normalizado (0 = disperso, 1 = un solo destino) y top-N."""
    part = g.valor_usd / g.valor_usd.sum()
    n = len(part)
    hhi = (part ** 2).sum()
    return pd.Series({
        "socios": n,
        "hhi": round(hhi, 4),
        "hhi_norm": round((hhi - 1 / n) / (1 - 1 / n), 4) if n > 1 else 1.0,
        "top1_pc": round(part.nlargest(1).sum() * 100, 1),
        "top4_pc": round(part.nlargest(4).sum() * 100, 1),
        "top10_pc": round(part.nlargest(10).sum() * 100, 1),
    })


conc = (paises[paises.flujo == "Exportacion"].groupby("anio")
        .apply(concentracion, include_groups=False).reset_index())
conc.to_csv(os.path.join(D, "hallazgo_concentracion.csv"), index=False)

print("CONCENTRACION DE LOS DESTINOS DE EXPORTACION")
print(conc.to_string(index=False))

eeuu = (paises[(paises.socio == "USA") & (paises.flujo == "Exportacion")]
        .set_index("anio").valor_usd)
tot_x = mundo.loc["Exportacion"]
dep = ((eeuu / tot_x) * 100).round(1).rename("dependencia_eeuu_pc").reset_index()
dep.to_csv(os.path.join(D, "hallazgo_dependencia_eeuu.csv"), index=False)
print("\nDEPENDENCIA DE ESTADOS UNIDOS (% de las exportaciones)")
print(dep.to_string(index=False))

# Que capitulos explican el crecimiento: aporte de cada uno al cambio total.
px = p[p.flujo == "Exportacion"]
ini, fin = px.anio.min(), px.anio.max()
piv = px.pivot_table(index=["cap_cod", "capitulo"], columns="anio",
                     values="valor_usd", aggfunc="sum").fillna(0)
piv["cambio"] = piv[fin] - piv[ini]
piv["aporte_pc"] = (piv["cambio"] / piv["cambio"].sum() * 100).round(1)
top = piv.nlargest(8, "cambio")[[ini, fin, "cambio", "aporte_pc"]].reset_index()
top.to_csv(os.path.join(D, "hallazgo_capitulos.csv"), index=False)
print(f"\nQUE EXPLICA EL CRECIMIENTO {ini}-{fin}")
vista = top.rename(columns={ini: f"{ini}_mmUSD", fin: f"{fin}_mmUSD",
                            "cambio": "cambio_mmUSD"})
for c in (f"{ini}_mmUSD", f"{fin}_mmUSD", "cambio_mmUSD"):
    vista[c] = (vista[c] / 1e9).round(2)
vista["capitulo"] = vista["capitulo"].str.slice(0, 46)
print(vista.to_string(index=False))

print("\nBalanza comercial (miles de millones USD)")
bal = (mundo.unstack(0).assign(saldo=lambda d: d.Exportacion - d.Importacion) / 1e9).round(2)
print(bal.tail(6).to_string())
bal.to_csv(os.path.join(D, "hallazgo_balanza.csv"))
