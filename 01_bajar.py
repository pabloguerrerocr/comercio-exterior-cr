"""Baja el comercio exterior de Costa Rica desde UN COMTRADE.

    python 01_bajar.py

API publica de Naciones Unidas. Todo se cachea en datos/cache/: la API limita
peticiones con HTTP 429 y el analisis tiene que poder rehacerse sin red.

Cosas del endpoint 'preview' averiguadas probandolo, no leyendo el manual:
  - partnerCode='all' devuelve HTTP 400. Hay que omitir el parametro.
  - Corta en 500 registros por respuesta. Por eso se pide una combinacion
    por vez (un anio, un flujo) en vez de todo junto.
  - NO devuelve partnerDesc ni cmdDesc: vienen en null. Los nombres salen de
    los catalogos de referencia, que son otro endpoint.
"""
import json
import os
import sys
import time

import pandas as pd
import requests

sys.stdout.reconfigure(encoding="utf-8")

AQUI = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(AQUI, "datos", "cache")
SALIDA = os.path.join(AQUI, "datos")
os.makedirs(CACHE, exist_ok=True)

API = "https://comtradeapi.un.org/public/v1/preview/C/A/HS"
REF = "https://comtradeapi.un.org/files/v1/app/reference"
CR = 188                                  # codigo M49 de Costa Rica
ANIOS = list(range(2010, 2025))
H = {"User-Agent": "Mozilla/5.0"}
ESPERA = 4.0                              # segundos entre peticiones


def cacheado(nombre, url, params=None):
    destino = os.path.join(CACHE, nombre + ".json")
    if os.path.exists(destino):
        return json.load(open(destino, encoding="utf-8"))
    for intento in range(4):
        r = requests.get(url, params=params, headers=H, timeout=90)
        if r.status_code == 200:
            d = r.json()
            json.dump(d, open(destino, "w", encoding="utf-8"))
            time.sleep(ESPERA)
            return d
        if r.status_code == 429:          # limite de peticiones: espera creciente
            espera = 20 * (intento + 1)
            print(f"    429, esperando {espera}s", flush=True)
            time.sleep(espera)
            continue
        r.raise_for_status()
    raise RuntimeError(f"no pude bajar {nombre}")


# ------------------------------------------------------------------ catalogos
print("Catalogos de referencia")
socios_ref = {int(x["PartnerCode"]): (x["PartnerDesc"], x.get("isGroup", False))
              for x in cacheado("ref_socios", f"{REF}/partnerAreas.json")["results"]
              if str(x.get("PartnerCode", "")).isdigit()}
hs_ref = {x["id"]: x["text"].split(" - ", 1)[-1]
          for x in cacheado("ref_hs", f"{REF}/HS.json")["results"]
          if x.get("aggrLevel") == 2}
print(f"  {len(socios_ref)} socios · {len(hs_ref)} capitulos HS\n")


def traer(anio, flujo, por_producto):
    p = {"reporterCode": CR, "period": anio, "flowCode": flujo}
    if por_producto:
        p.update({"partnerCode": 0, "cmdCode": "AG2"})
    else:
        p.update({"cmdCode": "TOTAL"})
    etiqueta = f"{'prod' if por_producto else 'socio'}_{anio}_{flujo}"
    return cacheado(etiqueta, API, p).get("data", [])


filas_socio, filas_prod = [], []
for anio in ANIOS:
    for flujo, nombre_flujo in (("X", "Exportacion"), ("M", "Importacion")):
        for f in traer(anio, flujo, False):
            cod = f.get("partnerCode")
            desc, es_grupo = socios_ref.get(cod, (f"cod {cod}", False))
            filas_socio.append({"anio": f.get("refYear"), "flujo": nombre_flujo,
                                "socio_cod": cod, "socio": desc, "es_agregado": es_grupo,
                                "valor_usd": f.get("primaryValue")})
        for f in traer(anio, flujo, True):
            cod = str(f.get("cmdCode"))
            filas_prod.append({"anio": f.get("refYear"), "flujo": nombre_flujo,
                               "cap_cod": cod, "capitulo": hs_ref.get(cod, f"cap {cod}"),
                               "valor_usd": f.get("primaryValue")})
    print(f"  {anio} ok", flush=True)

pd.DataFrame(filas_socio).to_csv(os.path.join(SALIDA, "comercio_por_socio.csv"),
                                 index=False, encoding="utf-8")
pd.DataFrame(filas_prod).to_csv(os.path.join(SALIDA, "comercio_por_producto.csv"),
                                index=False, encoding="utf-8")
print(f"\nsocios   {len(filas_socio):>6} filas")
print(f"productos {len(filas_prod):>5} filas")
print("CSV en datos/")
