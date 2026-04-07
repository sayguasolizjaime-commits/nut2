import os
from datetime import date
from dateutil.relativedelta import relativedelta

def cargar_lista(archivo):
    ruta = os.path.join(os.getcwd(), archivo)
    if os.path.exists(ruta):
        with open(ruta, "r", encoding="utf-8") as f:
            return [line.strip() for line in f.readlines()]
    return ["Otra"]

def calcular_edad_exacta(f_nac):
    if f_nac is None: return "Pendiente"
    hoy = date.today()
    delta = relativedelta(hoy, f_nac)
    return f"{delta.years} años, {delta.months} meses y {delta.days} días"