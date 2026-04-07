import streamlit as st

def calcular_indicadores():
    """
    Calcula IMC y otros indicadores leyendo correctamente
    desde st.session_state["datos_antropo"] (guardado por antropometria.py).
    Retorna un dict con los resultados o None si faltan datos.
    """
    datos = st.session_state.get("datos_antropo", None)

    if datos is None:
        return None

    try:
        peso = float(datos.loc[datos["Determinación"] == "Peso actual", "Dato"].values[0])
        talla = float(datos.loc[datos["Determinación"] == "Talla", "Dato"].values[0])
        peso_hab = float(datos.loc[datos["Determinación"] == "Peso habitual", "Dato"].values[0])

        if talla <= 0 or peso <= 0:
            return None

        imc = peso / (talla ** 2)

        # Clasificación IMC (OMS)
        if imc < 16:
            clasificacion = "Desnutrición severa"
        elif imc < 17:
            clasificacion = "Desnutrición moderada"
        elif imc < 18.5:
            clasificacion = "Bajo peso"
        elif imc < 25:
            clasificacion = "Normal"
        elif imc < 30:
            clasificacion = "Sobrepeso"
        elif imc < 35:
            clasificacion = "Obesidad grado I"
        elif imc < 40:
            clasificacion = "Obesidad grado II"
        else:
            clasificacion = "Obesidad grado III"

        # % pérdida de peso
        pct_perdida = 0.0
        if peso_hab > 0:
            pct_perdida = ((peso_hab - peso) / peso_hab) * 100

        return {
            "peso": peso,
            "talla": talla,
            "IMC": imc,
            "clasificacion": clasificacion,
            "pct_perdida": pct_perdida
        }

    except Exception:
        return None


def calcular_requerimientos(peso, talla, edad, sexo, formula="Mifflin-St Jeor"):
    """
    Calcula el Gasto Energético Total (GET) según la fórmula seleccionada.
    Retorna (TMB, GET_base) en kcal/día. Factor de actividad se aplica externamente.
    """
    if peso <= 0 or talla <= 0 or edad <= 0:
        return 0, {}

    talla_cm = talla * 100
    resultados = {}

    # --- Harris-Benedict (1919) ---
    if sexo == "Masculino":
        hb = 66.5 + (13.75 * peso) + (5.003 * talla_cm) - (6.775 * edad)
    else:
        hb = 655.1 + (9.563 * peso) + (1.850 * talla_cm) - (4.676 * edad)
    resultados["Harris-Benedict (1919)"] = round(hb, 1)

    # --- Mifflin-St Jeor ---
    if sexo == "Masculino":
        msj = (10 * peso) + (6.25 * talla_cm) - (5 * edad) + 5
    else:
        msj = (10 * peso) + (6.25 * talla_cm) - (5 * edad) - 161
    resultados["Mifflin-St Jeor"] = round(msj, 1)

    # --- OMS / FAO / UNU (por grupos de edad) ---
    if sexo == "Masculino":
        if edad < 3:    oms = (60.9 * peso) - 54
        elif edad < 10: oms = (22.7 * peso) + 495
        elif edad < 18: oms = (17.5 * peso) + 651
        elif edad < 30: oms = (15.3 * peso) + 679
        elif edad < 60: oms = (11.6 * peso) + 879
        else:           oms = (13.5 * peso) + 487
    else:
        if edad < 3:    oms = (61.0 * peso) - 51
        elif edad < 10: oms = (22.5 * peso) + 499
        elif edad < 18: oms = (12.2 * peso) + 746
        elif edad < 30: oms = (14.7 * peso) + 496
        elif edad < 60: oms = (8.7  * peso) + 829
        else:           oms = (10.5 * peso) + 596
    resultados["OMS / FAO / UNU"] = round(oms, 1)

    # --- Roza y Shizgal (1984) ---
    if sexo == "Masculino":
        roza = (13.707 * peso) + (492.3 * talla) - (6.673 * edad) + 77.607
    else:
        roza = (9.740 * peso) + (172.9 * talla) - (4.737 * edad) + 667.051
    resultados["Roza y Shizgal (1984)"] = round(roza, 1)

    tmb_seleccionada = resultados.get(formula, msj)
    return tmb_seleccionada, resultados
