"""Genera las figuras del README.

    python 06_figuras.py

Un README sin imagen obliga a clonar el repo para ver un resultado. Tres
figuras que cuentan el hallazgo sin leer nada.
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(AQUI, "datos")
FIG = os.path.join(AQUI, "figuras")
os.makedirs(FIG, exist_ok=True)

NARANJA, AZUL, GRIS = "#e8590c", "#1c7ed6", "#adb5bd"
plt.rcParams.update({"font.size": 11, "axes.spines.top": False,
                     "axes.spines.right": False, "figure.facecolor": "white",
                     "axes.grid": True, "grid.alpha": .25, "grid.linestyle": "-"})

conc = pd.read_csv(os.path.join(D, "hallazgo_concentracion.csv"))
socio = pd.read_csv(os.path.join(D, "comercio_por_socio.csv"))
cap = pd.read_csv(os.path.join(D, "hallazgo_capitulos.csv"))


def cerrar(fig, nombre, titulo, sub):
    fig.suptitle(titulo, fontsize=15, fontweight="bold", x=.02, ha="left", y=.98)
    fig.text(.02, .915, sub, fontsize=10.5, color="#555")
    fig.tight_layout(rect=[0, 0, 1, .89])
    ruta = os.path.join(FIG, nombre)
    fig.savefig(ruta, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print("  ", nombre)


# 1 ── la concentracion sube
fig, ax = plt.subplots(figsize=(11, 5.2))
ax.plot(conc.anio, conc.top1_pc, "o-", color=NARANJA, lw=2.5, label="Estados Unidos solo")
ax.plot(conc.anio, conc.top4_pc, "s-", color=AZUL, lw=2.5, label="los 4 mayores destinos")
ax.plot(conc.anio, conc.top10_pc, "^-", color=GRIS, lw=2, label="los 10 mayores destinos")
for x, y in [(conc.anio.iloc[0], conc.top1_pc.iloc[0]), (conc.anio.iloc[-1], conc.top1_pc.iloc[-1])]:
    ax.annotate(f"{y:.1f}%", (x, y), textcoords="offset points", xytext=(0, 11),
                ha="center", fontweight="bold", color=NARANJA)
ax.set_ylabel("% de las exportaciones")
ax.set_ylim(30, 90)
ax.legend(frameon=False, loc="center left")
cerrar(fig, "01_concentracion.png", "La concentración subió todos los años",
       "Participación en las exportaciones totales de Costa Rica, 2010-2024.")

# 2 ── quien explica el crecimiento
c = cap.sort_values("cambio").tail(8)
fig, ax = plt.subplots(figsize=(11, 5.6))
col = [NARANJA if a > 20 else AZUL for a in c.aporte_pc]
ax.barh([t[:44] for t in c.capitulo], c.cambio / 1e9, color=col)
for i, (v, a) in enumerate(zip(c.cambio / 1e9, c.aporte_pc)):
    ax.text(v + .12, i, f"{a:.1f}% del crecimiento", va="center", fontsize=9.5, color="#444")
ax.set_xlabel("cambio en las exportaciones 2010-2024, miles de millones USD")
ax.set_xlim(0, (c.cambio / 1e9).max() * 1.42)
cerrar(fig, "02_capitulos.png", "Un solo capítulo explica el 70% del crecimiento",
       "Instrumentos médicos, ópticos y de precisión (capítulo 90 del sistema armonizado).")

# 3 ── exportaciones e importaciones
mundo = socio[socio.socio_cod == 0].pivot_table(index="anio", columns="flujo",
                                                values="valor_usd") / 1e9
fig, ax = plt.subplots(figsize=(11, 5.2))
ax.fill_between(mundo.index, mundo.Exportacion, mundo.Importacion,
                color=NARANJA, alpha=.13)
ax.plot(mundo.index, mundo.Exportacion, "o-", color=AZUL, lw=2.5, label="exportaciones")
ax.plot(mundo.index, mundo.Importacion, "s-", color=NARANJA, lw=2.5, label="importaciones")
ax.set_ylabel("miles de millones de USD")
ax.legend(frameon=False, loc="upper left")
ax.annotate(f"déficit\n{mundo.Exportacion.iloc[-1] - mundo.Importacion.iloc[-1]:.1f} mm",
            (mundo.index[-1], (mundo.Exportacion.iloc[-1] + mundo.Importacion.iloc[-1]) / 2),
            textcoords="offset points", xytext=(-52, 0), fontsize=10, color=NARANJA,
            fontweight="bold", ha="center")
cerrar(fig, "03_balanza.png", "El déficit comercial es persistente",
       "Costa Rica importa más de lo que exporta todos los años del período.")

print("\nFiguras en figuras/")
