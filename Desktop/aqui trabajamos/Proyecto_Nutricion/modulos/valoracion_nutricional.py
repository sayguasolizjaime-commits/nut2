import streamlit as st
import pandas as pd
from datetime import datetime
import json
import os

# --- CARGA DE DATOS (PROTEGIDA) ---
@st.cache_data
def cargar_vademecum_json():
    ruta = "medicamentos.json"
    if os.path.exists(ruta):
        try:
            with open(ruta, "r", encoding="utf-8") as f: return json.load(f).get("vademecum", [])
        except: return []
    return []

@st.cache_data
def cargar_vademecum_fito_json():
    ruta = "fitoterapia.json"
    if os.path.exists(ruta):
        try:
            with open(ruta, "r", encoding="utf-8") as f: return json.load(f).get("plantas", [])
        except: return []
    return []

@st.cache_data
def cargar_biblioteca():
    ruta = "biblioteca.json"
    if os.path.exists(ruta):
        try:
            with open(ruta, "r", encoding="utf-8") as f: return json.load(f)
        except: return {}
    return {}

# ================================================================
# FUNCIÓN: Calcula GER según fórmula
# ================================================================
def calcular_ger(peso, talla, edad, sexo, formula):
    talla_cm = talla * 100
    if formula == "Harris-Benedict (1919)":
        if sexo == "Masculino":
            return 66.5 + (13.75 * peso) + (5.003 * talla_cm) - (6.775 * edad)
        else:
            return 655.1 + (9.563 * peso) + (1.850 * talla_cm) - (4.676 * edad)
    elif formula == "Mifflin-St Jeor":
        if sexo == "Masculino":
            return (10 * peso) + (6.25 * talla_cm) - (5 * edad) + 5
        else:
            return (10 * peso) + (6.25 * talla_cm) - (5 * edad) - 161
    elif formula == "OMS / FAO / UNU":
        if sexo == "Masculino":
            if edad < 3:    return (60.9 * peso) - 54
            elif edad < 10: return (22.7 * peso) + 495
            elif edad < 18: return (17.5 * peso) + 651
            elif edad < 30: return (15.3 * peso) + 679
            elif edad < 60: return (11.6 * peso) + 879
            else:           return (13.5 * peso) + 487
        else:
            if edad < 3:    return (61.0 * peso) - 51
            elif edad < 10: return (22.5 * peso) + 499
            elif edad < 18: return (12.2 * peso) + 746
            elif edad < 30: return (14.7 * peso) + 496
            elif edad < 60: return (8.7  * peso) + 829
            else:           return (10.5 * peso) + 596
    elif formula == "Roza y Shizgal (1984)":
        if sexo == "Masculino":
            return (13.707 * peso) + (492.3 * talla) - (6.673 * edad) + 77.607
        else:
            return (9.740 * peso) + (172.9 * talla) - (4.737 * edad) + 667.051
    elif formula == "Valencia":
        if sexo == "Masculino":
            return (10.5 * peso) + (940 * talla) - 97
        else:
            return (9.99 * peso) + (6.25 * talla_cm) - (4.92 * edad) - 161
    return 0.0

# ================================================================
# FUNCIÓN: Bloque de cálculo energético completo (Punto A o B)
# ================================================================
def bloque_calculo_energetico(label, peso, talla, edad, sexo, formula, key_prefix):
    st.markdown(f"### {label}")
    st.markdown(f"**Datos:** Peso: `{peso:.2f} kg` | Talla: `{talla:.3f} m` | Edad: `{edad}` años | Sexo: `{sexo}`")
    st.markdown(f"**Fórmula:** `{formula}`")

    ger = calcular_ger(peso, talla, edad, sexo, formula)
    if ger <= 0:
        st.warning("⚠️ Faltan datos para calcular el GER.")
        return

    ger_h = ger / 24
    st.success(f"**GER = {ger:.2f} Kcal/día** ({ger_h:.2f} Kcal/hora)")
    st.markdown("---")

    # ── TABLA DE ACTIVIDAD FÍSICA ──────────────────────────────
    st.markdown("#### Actividad Física")

    key_tabla = f"df_act_{key_prefix}"
    tabla_act = st.session_state.get("tabla_actividades", pd.DataFrame())

    if not tabla_act.empty and "Actividad" in tabla_act.columns and "Minutos" in tabla_act.columns:
        filas_sync = []
        for _, row in tabla_act.iterrows():
            horas = round(float(row.get("Minutos", 0)) / 60, 1)
            met   = float(row.get("MET", 1.2))
            act   = str(row.get("Actividad", ""))
            if horas > 0:
                filas_sync.append({"Actividad": act, "Factor": met, "Horas": horas})
        st.session_state[key_tabla] = pd.DataFrame(filas_sync) if filas_sync else pd.DataFrame(columns=["Actividad", "Factor", "Horas"])
    elif key_tabla not in st.session_state:
        st.session_state[key_tabla] = pd.DataFrame(columns=["Actividad", "Factor", "Horas"])

    df_act_edit = st.data_editor(
        st.session_state[key_tabla],
        num_rows="dynamic",
        use_container_width=True,
        key=f"editor_act_{key_prefix}",
        column_config={
            "Actividad": st.column_config.TextColumn("Actividad"),
            "Factor": st.column_config.NumberColumn("Factor MET", min_value=0.5, max_value=20.0, step=0.1, format="%.1f"),
            "Horas": st.column_config.NumberColumn("Horas", min_value=0.0, max_value=24.0, step=0.5, format="%.1f"),
        },
        hide_index=True,
    )
    st.session_state[key_tabla] = df_act_edit

    df_valido = df_act_edit.dropna(subset=["Factor", "Horas"])
    df_valido = df_valido[df_valido["Horas"].astype(float) > 0] if not df_valido.empty else df_valido

    total_horas = float(df_valido["Horas"].sum()) if not df_valido.empty else 0.0
    filas_res   = []
    ete_total   = 0.0

    if df_valido.empty:
        st.info("💡 Ingrese actividades en la tabla para calcular el gasto energético.")
    else:
        for _, row in df_valido.iterrows():
            factor    = float(row["Factor"]) if row["Factor"] is not None else 1.0
            horas     = float(row["Horas"])
            ger_h_act = ger_h * factor
            kcal_act  = ger_h_act * horas
            ete_total += kcal_act
            filas_res.append({
                "Actividad": str(row["Actividad"]) if row["Actividad"] else "", "Factor": factor,
                "Tiempo (h)": horas, "GER/H": round(ger_h_act, 2),
                "Total Kcal": round(kcal_act, 2)
            })

        df_res = pd.DataFrame(filas_res)
        fila_t = pd.DataFrame([{"Actividad": "TOTAL", "Factor": "",
                                 "Tiempo (h)": round(total_horas, 1),
                                 "GER/H": "", "Total Kcal": round(ete_total, 2)}])
        st.dataframe(pd.concat([df_res, fila_t], ignore_index=True),
                     use_container_width=True, hide_index=True)

        if abs(total_horas - 24.0) > 0.1:
            st.warning(f"⚠️ Las horas suman {total_horas:.1f}h — deben sumar 24h.")
        else:
            st.success("✅ Horas correctas: 24h.")

    st.markdown("---")

    # Resumen energético
    st.markdown("#### Resumen Energético")
    eta = ete_total * 0.10

    st.markdown("**Factor de Patología (TF)**")
    lista_dx     = st.session_state.get("v_dx_multi", [])
    bib_local    = cargar_biblioteca()
    fp_por_dx    = [{"Diagnóstico": dx, "FP": bib_local.get(dx, {}).get("fp", 1.0)} for dx in lista_dx]
    fp_automatico = max([x["FP"] for x in fp_por_dx], default=1.0)

    if fp_por_dx:
        df_fp = pd.DataFrame(fp_por_dx)
        df_fp["Estado"] = df_fp["FP"].apply(lambda x: "✅ DOMINANTE" if x == fp_automatico else "")
        st.dataframe(df_fp, use_container_width=True, hide_index=True)
        st.success(f"Factor dominante detectado: **{fp_automatico}** — puede ajustarlo si lo considera necesario.")
    else:
        st.info("Sin diagnósticos registrados. Ingrese el factor manualmente.")

    col_fp1, col_fp2 = st.columns([2, 1])
    with col_fp1:
        fp = st.number_input(
            "Factor de Patología (ajustable):",
            min_value=0.5, max_value=3.0,
            value=float(fp_automatico),
            step=0.1,
            key=f"fp_custom_{key_prefix}",
        )
    with col_fp2:
        st.metric("Factor aplicado", f"{fp}")

    tf         = ete_total * (fp - 1.0)
    total_kcal = ete_total + eta + tf

    df_resumen = pd.DataFrame([
        {"Componente": "GET  (Gasto Energético Total — actividad)", "Kcal": round(ete_total, 2)},
        {"Componente": "ETA  (Efecto Térmico Alimentos — 10%)",     "Kcal": round(eta, 2)},
        {"Componente": f"TF   (Factor Patología × {fp})",            "Kcal": round(tf, 2)},
        {"Componente": "TOTAL REQUERIMIENTO ENERGÉTICO",             "Kcal": round(total_kcal, 2)},
    ])
    st.dataframe(df_resumen, use_container_width=True, hide_index=True)

    cr1, cr2, cr3 = st.columns(3)
    cr1.metric("GER", f"{ger:.2f} Kcal")
    cr2.metric("ETE", f"{ete_total:.2f} Kcal")
    cr3.metric("🎯 TOTAL", f"{total_kcal:.2f} Kcal")

    st.markdown("---")

    # Macronutrientes
    st.markdown("#### Distribución de Macronutrientes")
    cm1, cm2, cm3 = st.columns(3)
    pct_p = cm1.number_input("% Proteínas", 0, 100, 10, 1, key=f"pct_p_{key_prefix}")
    pct_l = cm2.number_input("% Lípidos",   0, 100, 30, 1, key=f"pct_l_{key_prefix}")
    pct_h = cm3.number_input("% H.C.",       0, 100, 60, 1, key=f"pct_h_{key_prefix}")

    if (pct_p + pct_l + pct_h) != 100:
        st.warning(f"⚠️ Los porcentajes suman {pct_p+pct_l+pct_h}% — deben sumar 100%.")
    else:
        kcal_p = total_kcal * (pct_p / 100)
        kcal_l = total_kcal * (pct_l / 100)
        kcal_h = total_kcal * (pct_h / 100)
        df_macro = pd.DataFrame([
            {"Nutriente": "Proteínas", "%": pct_p, "Gramos": round(kcal_p/4, 2), "Kcal": round(kcal_p, 2)},
            {"Nutriente": "Lípidos",   "%": pct_l, "Gramos": round(kcal_l/9, 2), "Kcal": round(kcal_l, 2)},
            {"Nutriente": "H.C.",      "%": pct_h, "Gramos": round(kcal_h/4, 2), "Kcal": round(kcal_h, 2)},
            {"Nutriente": "TOTAL",     "%": 100,   "Gramos": round(kcal_p/4+kcal_l/9+kcal_h/4, 2),
             "Kcal": round(total_kcal, 2)},
        ])
        st.dataframe(df_macro, use_container_width=True, hide_index=True)
        st.session_state[f"macro_{key_prefix}"] = {
            "total_kcal": round(total_kcal, 2),
            "gr_prot": round(kcal_p/4, 2),
            "gr_lip":  round(kcal_l/9, 2),
            "gr_hc":   round(kcal_h/4, 2),
        }

# ================================================================
# FUNCIÓN PRINCIPAL
# ================================================================
def render_valoracion_nutricional():
    st.header("🔬 VALORACIÓN NUTRICIONAL")
    st.markdown("---")

    # Datos comunes heredados desde session_state
    paciente      = st.session_state.get("paciente", {})
    f_nom         = paciente.get("nombre",       st.session_state.get("f_nombre", "Paciente"))
    f_eda         = paciente.get("edad",         st.session_state.get("f_edad", 0))
    f_sex         = paciente.get("sexo",         st.session_state.get("f_sexo", "N/A"))
    f_civ         = paciente.get("estado_civil", st.session_state.get("f_estado_civil", "N/A"))
    f_ocu         = paciente.get("ocupacion",    st.session_state.get("f_ocupacion", "N/A"))
    f_pes         = st.session_state.get("a_peso", 0.0)
    f_tal         = st.session_state.get("a_talla", 0.0)
    biblioteca    = cargar_biblioteca()
    vademecum     = cargar_vademecum_json()
    vademecum_fito= cargar_vademecum_fito_json()

    # ================================================================
    # 8 PESTAÑAS PRINCIPALES
    # ================================================================
    tabs = st.tabs([
        "1. Datos del Paciente",
        "2. A. Patologías Actuales",
        "3. A. Datos Alimentarios",
        "4. Necesidades Energéticas",
        "5. A. Indicadores Bioquímicos",
        "6. Evaluación Antropométrica",
        "7. Evaluación del C.A.P.",
        "8. Diagnóstico Final Nutricional",
    ])

    # ================================================================
    # PESTAÑA 1 — DATOS DEL PACIENTE
    # ================================================================
    with tabs[0]:
        st.subheader("I. FICHA DE FILIACIÓN")

        c1, c2, c3 = st.columns([1, 2, 1])
        c1.text_input("N° HCL",         value=str(st.session_state.get("f_hcl", "0000")), disabled=True, key="vn_hcl")
        c2.text_input("Nombre Completo", value=str(f_nom),  disabled=True, key="vn_nom")
        c3.text_input("Fecha",           value=datetime.now().strftime("%d/%m/%Y"), disabled=True, key="vn_fec")

        c4, c5, c6, c7 = st.columns(4)
        c4.number_input("Edad",       value=int(f_eda),   disabled=True, key="vn_edad")
        c5.text_input("Sexo",         value=str(f_sex),   disabled=True, key="vn_sexo")
        c6.number_input("Peso (kg)",  value=float(f_pes), disabled=True, key="vn_peso")
        c7.number_input("Talla (m)",  value=float(f_tal), disabled=True, key="vn_talla")

        c8, c9, c10 = st.columns(3)
        c8.text_input("Estado Civil",  value=str(f_civ), disabled=True, key="vn_civ")
        c9.text_input("Procedencia",   value=str(st.session_state.get("f_procedencia", "N/A")), disabled=True, key="vn_proc")
        c10.text_input("Religión",     value=str(st.session_state.get("f_religion", "N/A")),    disabled=True, key="vn_rel")

        c11, c12 = st.columns(2)
        c11.text_input("Instrucción",  value=str(st.session_state.get("f_instruccion", "N/A")), disabled=True, key="vn_ins")
        c12.text_input("Ocupación",    value=str(f_ocu), disabled=True, key="vn_ocu")

        if not f_nom or f_nom == "Paciente":
            st.warning("⚠️ Complete y guarde los datos en Recolección → Filiación para ver el resumen aquí.")

    # ================================================================
    # PESTAÑA 2 — PATOLOGÍAS ACTUALES
    # ================================================================
    with tabs[1]:
        st.subheader("II. ANÁLISIS DE PATOLOGÍAS Y ANTECEDENTES")

        # 1. Diagnósticos actuales
        st.markdown("#### 1. Patologías Actuales")
        lista_dx = st.session_state.get("v_dx_multi", [])
        if not lista_dx:
            st.info("Sin diagnósticos registrados. Complete Recolección → Datos Médicos.")
        else:
            for dx in lista_dx:
                datos = biblioteca.get(dx, {"pred": "", "fisi": "", "imp": ""})
                with st.expander(f"📚 ANÁLISIS CIENTÍFICO: {dx}", expanded=True):
                    col_a, col_b = st.columns([1, 1.5])
                    with col_a:
                        st.text_area(f"Mecanismos ({dx})", value=datos.get("pred",""), height=120, key=f"v_mec_{dx}")
                    with col_b:
                        st.text_area("Fisiopatología", value=datos.get("fisi",""), height=60, key=f"v_fis_{dx}")
                        st.text_area("Implicaciones",  value=datos.get("imp",""),  height=60, key=f"v_imp_{dx}")

        st.markdown("---")

        # 2. Antecedentes personales
        st.markdown("#### 2. Antecedentes Personales")
        lista_ant = st.session_state.get("m_ant_p_json", [])
        if not lista_ant:
            st.info("Sin antecedentes personales registrados.")
        else:
            for ant in lista_ant:
                datos_p = biblioteca.get(ant, {"fisi": "N/A", "imp": "N/A"})
                with st.expander(f"📜 ANTECEDENTE PERSONAL: {ant}", expanded=True):
                    cp1, cp2 = st.columns(2)
                    cp1.text_area("Fisiopatología Crónica", value=datos_p.get("fisi","N/A"), height=80, key=f"v_ap_f_{ant}")
                    cp2.text_area("Impacto Nutricional",    value=datos_p.get("imp","N/A"),  height=80, key=f"v_ap_i_{ant}")

        st.markdown("---")

        # 3. Antecedentes familiares
        st.markdown("#### 3. Antecedentes Familiares")
        lista_fam = st.session_state.get("m_ant_f_json", [])
        if not lista_fam:
            st.info("Sin antecedentes familiares registrados.")
        else:
            for idx, item in enumerate(lista_fam):
                nombre_v = item.get("descripcion_visual") if isinstance(item, dict) else item
                clave_t  = item.get("patologia_clave")    if isinstance(item, dict) else item
                datos_f  = biblioteca.get(clave_t, {"fisi": "N/A", "imp": "N/A"})
                with st.expander(f"🧬 HERENCIA: {nombre_v}", expanded=True):
                    cf1, cf2 = st.columns(2)
                    cf1.text_area("Predisposición", value=datos_f.get("fisi","N/A"), height=80, key=f"v_af_f_{idx}")
                    cf2.text_area("Riesgo",         value=datos_f.get("imp","N/A"),  height=80, key=f"v_af_i_{idx}")

        st.markdown("---")

        # 4. Farmacoterapia
        st.markdown("#### 4. Análisis Científico de Farmacoterapia")
        meds_rows = st.session_state.get("ed_meds", {}).get("rows", [])
        if not meds_rows:
            st.info("Sin medicamentos registrados.")
        else:
            for idx, fila in enumerate(meds_rows):
                nombre_sel = fila.get("Medicamento", "").split(" (")[0].strip()
                info = next((m for m in vademecum if m["quimico"].lower() == nombre_sel.lower()), None)
                if info:
                    st.markdown(f"💊 **{info['quimico']}**")
                    cfa1, cfa2 = st.columns(2)
                    with cfa1:
                        st.error(f"🚫 Evitar: {info['alimentos_a_evitar']}")
                        st.text_area(f"Interacción ({idx})",   value=info['interaccion_farma_nutri'], height=80, key=f"v_fa_int_{idx}")
                    with cfa2:
                        st.success(f"💡 Sugerencia: {info['recomendacion']}")
                        st.text_area(f"Recomendación ({idx})", value=info['recomendacion'],           height=80, key=f"v_fa_rec_{idx}")

        st.markdown("---")

        # 5. Fitoterapia
        st.markdown("#### 5. Análisis Científico de Fitoterapia")
        fito_data = st.session_state.get("ed_fito_datos", [])
        if not fito_data:
            st.info("Sin fitoterapia registrada.")
        else:
            for idx, item in enumerate(fito_data):
                nombre_fito = item.get("Planta")
                info_fito   = next((p for p in vademecum_fito if p["nombre"].lower() == nombre_fito.lower()), None)
                if info_fito:
                    with st.expander(f"🌿 PLANTA: {nombre_fito}", expanded=True):
                        cfit1, cfit2 = st.columns(2)
                        cfit1.text_area("Interacción", value=info_fito['interaccion_nutri'], height=80, key=f"v_fit_i_{idx}")
                        cfit2.text_area("Sugerencia",  value=info_fito['sugerencia'],        height=80, key=f"v_fit_s_{idx}")

        st.markdown("---")
        st.text_area("📝 Juicio Clínico Integrado:", key="v_juicio_clinico")

    # ================================================================
    # PESTAÑA 3 — DATOS ALIMENTARIOS (Análisis del R24h + dieta)
    # ================================================================
    with tabs[2]:
        st.subheader("III. ANÁLISIS DEL RECORDATORIO DE 24 HORAS")
        st.markdown("---")

        def obtener_rda(sexo, edad):
            es_mujer = sexo in ["Femenino", "Mujer", "F"]
            rda = {
                "Energia":  1800 if es_mujer else 2000,
                "Prot.":    46   if es_mujer else 56,
                "grasas":   55   if es_mujer else 65,
                "H C":      260  if es_mujer else 300,
                "Fribra":   25   if es_mujer else 38,
                "Ca.":      1000,
                "Fosforo":  700,
                "Fe.":      18   if es_mujer else 8,
                "Vit. A":   700  if es_mujer else 900,
                "B1":       1.1  if es_mujer else 1.2,
                "B2":       1.1  if es_mujer else 1.3,
                "Niacina":  14   if es_mujer else 16,
                "Vit C":    75   if es_mujer else 90,
            }
            if edad >= 65:
                rda["Ca."] = 1200
            if edad < 18:
                rda["Ca."] = 1300
                rda["Fe."] = 15 if es_mujer else 11
            return rda

        NUTRIENTES_VN = {
            "Energia": "Energía (Kcal)", "Prot.": "Proteínas (g)", "grasas": "Grasas (g)",
            "H C": "H.C. (g)", "Fribra": "Fibra (g)", "Ca.": "Calcio (mg)",
            "Fosforo": "Fósforo (mg)", "Fe.": "Hierro (mg)", "Vit. A": "Vit. A (mcg)",
            "B1": "B1 (mg)", "B2": "B2 (mg)", "Niacina": "Niacina (mg)", "Vit C": "Vit. C (mg)",
        }
        UNIDADES = {
            "Energia": "Kcal", "Prot.": "g", "grasas": "g", "H C": "g",
            "Fribra": "g", "Ca.": "mg", "Fosforo": "mg", "Fe.": "mg",
            "Vit. A": "mcg", "B1": "mg", "B2": "mg", "Niacina": "mg", "Vit C": "mg"
        }

        def calc_nut(df_base, alimento, gramos):
            match = df_base[df_base["ALIMENTO"] == alimento]
            if match.empty or gramos <= 0:
                return {k: 0.0 for k in NUTRIENTES_VN}
            factor = gramos / 100
            return {k: round(float(pd.to_numeric(match[k].values[0], errors="coerce") or 0) * factor, 3)
                    for k in NUTRIENTES_VN}

        def sumar_nut(lista):
            total = {k: 0.0 for k in NUTRIENTES_VN}
            for d in lista:
                for k in NUTRIENTES_VN:
                    total[k] += d.get(k, 0.0)
            return {k: round(v, 2) for k, v in total.items()}

        r24h_dias      = st.session_state.get("r24h_dias", {})
        dias_con_datos = {d: df for d, df in r24h_dias.items() if isinstance(df, pd.DataFrame) and not df.empty}

        if not dias_con_datos:
            st.info("💡 Registre y guarde los días en Recolección → Datos Alimentarios → R24h.")
        else:
            df_base_vn = None
            if os.path.exists("base.xlsx"):
                try:
                    df_base_vn = pd.read_excel("base.xlsx")
                    df_base_vn.columns = df_base_vn.columns.str.strip()
                except:
                    pass

            sexo_vn = paciente.get("sexo", st.session_state.get("f_sexo", "Masculino"))
            edad_vn = int(paciente.get("edad", st.session_state.get("f_edad", 30)))
            rda     = obtener_rda(sexo_vn, edad_vn)
            totales_dias = {}

            for dia, df_dia in dias_con_datos.items():
                tipo_dia = st.session_state.get("r24h_tipos", {}).get(dia, "Día de semana")
                guardado = st.session_state.get(f"r24h_{dia}_guardado", False)
                st.markdown(f"### {'✅' if guardado else '⚠️'} {dia} — {tipo_dia}")

                nut_dia_lista = []
                tiempos_orden = ["Desayuno", "Media Mañana", "Almuerzo", "Merienda", "Cena"]
                tiempos_en_dia = df_dia["Tiempo"].unique()

                for tiempo in tiempos_orden:
                    if tiempo not in tiempos_en_dia:
                        continue
                    df_t = df_dia[df_dia["Tiempo"] == tiempo]
                    nut_tiempo = []
                    for _, row in df_t.iterrows():
                        n = calc_nut(df_base_vn, row["Alimento"], float(row["Gramos"])) if df_base_vn is not None else {k: 0.0 for k in NUTRIENTES_VN}
                        nut_tiempo.append(n)
                        nut_dia_lista.append(n)

                    total_tiempo = sumar_nut(nut_tiempo)
                    with st.expander(f"🍽️ {tiempo}", expanded=False):
                        filas = []
                        for _, row in df_t.iterrows():
                            n = calc_nut(df_base_vn, row["Alimento"], float(row["Gramos"])) if df_base_vn is not None else {k: 0.0 for k in NUTRIENTES_VN}
                            fila = {"Alimento": row["Alimento"], "Gramos": row["Gramos"]}
                            fila.update({NUTRIENTES_VN[k]: v for k, v in n.items()})
                            filas.append(fila)
                        st.dataframe(pd.DataFrame(filas), use_container_width=True, hide_index=True)
                        st.markdown("**Subtotal:**")
                        st.dataframe(pd.DataFrame([{NUTRIENTES_VN[k]: v for k, v in total_tiempo.items()}]), use_container_width=True, hide_index=True)

                total_dia = sumar_nut(nut_dia_lista)
                totales_dias[dia] = total_dia
                st.markdown(f"**📊 Total {dia}:**")
                st.dataframe(pd.DataFrame([{NUTRIENTES_VN[k]: v for k, v in total_dia.items()}]), use_container_width=True, hide_index=True)
                st.markdown("---")

            # Promedio y comparación con RDA
            n_dias = len(totales_dias)
            if n_dias > 0:
                st.markdown(f"## 📈 Consolidado — Promedio de {n_dias} día(s)")
                prom = {k: round(sum(totales_dias[d].get(k, 0) for d in totales_dias) / n_dias, 2) for k in NUTRIENTES_VN}

                filas_comp = []
                for k, nombre in NUTRIENTES_VN.items():
                    consumo = prom[k]
                    rda_val = rda.get(k, 0)
                    pct_rda = round((consumo / rda_val) * 100, 1) if rda_val > 0 else 0.0
                    unidad  = UNIDADES.get(k, "")
                    if pct_rda == 0:     estado = "—"
                    elif pct_rda < 67:   estado = "🔴 Deficiente"
                    elif pct_rda < 90:   estado = "🟡 Bajo"
                    elif pct_rda <= 110: estado = "🟢 Adecuado"
                    elif pct_rda <= 150: estado = "🟠 Alto"
                    else:                estado = "🔴 Excesivo"
                    filas_comp.append({"Nutriente": nombre, "Unidad": unidad,
                                       "Consumo Prom.": consumo, "RDA/IDR": rda_val,
                                       "% Adecuación": f"{pct_rda}%", "Estado": estado})

                st.dataframe(pd.DataFrame(filas_comp), use_container_width=True, hide_index=True)

                macro_pta = st.session_state.get("macro_pta", {})
                macro_ptb = st.session_state.get("macro_ptb", {})
                if macro_pta or macro_ptb:
                    def pct2(c, r): return round((c/r)*100, 1) if r > 0 else 0.0
                    st.markdown("### Comparación con Requerimientos Calculados")
                    df_req = pd.DataFrame([
                        {"Nutriente": "Energía (Kcal)", "Consumo Prom.": prom["Energia"],
                         "Req. Peso Ideal": macro_pta.get("total_kcal", 0), "% Adec. A": f"{pct2(prom['Energia'], macro_pta.get('total_kcal',0))}%",
                         "Req. Peso Actual": macro_ptb.get("total_kcal", 0), "% Adec. B": f"{pct2(prom['Energia'], macro_ptb.get('total_kcal',0))}%"},
                        {"Nutriente": "Proteínas (g)", "Consumo Prom.": prom["Prot."],
                         "Req. Peso Ideal": macro_pta.get("gr_prot", 0), "% Adec. A": f"{pct2(prom['Prot.'], macro_pta.get('gr_prot',0))}%",
                         "Req. Peso Actual": macro_ptb.get("gr_prot", 0), "% Adec. B": f"{pct2(prom['Prot.'], macro_ptb.get('gr_prot',0))}%"},
                        {"Nutriente": "Grasas (g)", "Consumo Prom.": prom["grasas"],
                         "Req. Peso Ideal": macro_pta.get("gr_lip", 0), "% Adec. A": f"{pct2(prom['grasas'], macro_pta.get('gr_lip',0))}%",
                         "Req. Peso Actual": macro_ptb.get("gr_lip", 0), "% Adec. B": f"{pct2(prom['grasas'], macro_ptb.get('gr_lip',0))}%"},
                        {"Nutriente": "H.C. (g)", "Consumo Prom.": prom["H C"],
                         "Req. Peso Ideal": macro_pta.get("gr_hc", 0), "% Adec. A": f"{pct2(prom['H C'], macro_pta.get('gr_hc',0))}%",
                         "Req. Peso Actual": macro_ptb.get("gr_hc", 0), "% Adec. B": f"{pct2(prom['H C'], macro_ptb.get('gr_hc',0))}%"},
                    ])
                    st.dataframe(df_req, use_container_width=True, hide_index=True)

                st.session_state["r24h_promedio"] = {**{k: prom[k] for k in NUTRIENTES_VN}, "n_dias": n_dias}

        # Análisis de la dieta
        st.markdown("---")
        st.subheader("IV. ANÁLISIS DE LA DIETA")
        st.markdown("---")

        prom_vn   = st.session_state.get("r24h_promedio", {})
        macro_pta = st.session_state.get("macro_pta", {})
        macro_ptb = st.session_state.get("macro_ptb", {})

        def evaluar_dieta(prom, macro_a, macro_b, r24h_dias):
            resultados = {}
            kcal_c = prom.get("Energia", 0)
            req_a  = macro_a.get("total_kcal", 0)
            req_b  = macro_b.get("total_kcal", 0)
            if req_a > 0:
                pct_a = round((kcal_c / req_a) * 100, 1)
                pct_b = round((kcal_c / req_b) * 100, 1) if req_b > 0 else 0
                if pct_a < 90:
                    eval_c, icon_c = f"No cubre el requerimiento energético — consume el {pct_a}% del requerimiento para peso ideal y {pct_b}% para peso actual.", "🔴"
                elif pct_a > 110:
                    eval_c, icon_c = f"Excede el requerimiento energético — consume el {pct_a}% del requerimiento para peso ideal y {pct_b}% para peso actual.", "🟠"
                else:
                    eval_c, icon_c = f"Cubre adecuadamente el requerimiento energético — {pct_a}% para peso ideal y {pct_b}% para peso actual.", "🟢"
            else:
                eval_c, icon_c = "Sin datos de requerimiento. Complete los Puntos A y B.", "⬜"
            resultados["Completa"] = (icon_c, eval_c)

            prot_c = prom.get("Prot.", 0); lip_c = prom.get("grasas", 0); hc_c = prom.get("H C", 0)
            kcal_mac = (prot_c * 4) + (lip_c * 9) + (hc_c * 4)
            if kcal_mac > 0:
                pct_prot = round((prot_c * 4 / kcal_mac) * 100, 1)
                pct_lip  = round((lip_c  * 9 / kcal_mac) * 100, 1)
                pct_hc   = round((hc_c   * 4 / kcal_mac) * 100, 1)
                problemas = []
                if pct_prot < 8:   problemas.append(f"proteínas bajas ({pct_prot}%)")
                if pct_prot > 20:  problemas.append(f"proteínas altas ({pct_prot}%)")
                if pct_lip < 20:   problemas.append(f"grasas bajas ({pct_lip}%)")
                if pct_lip > 35:   problemas.append(f"grasas altas ({pct_lip}%)")
                if pct_hc < 45:    problemas.append(f"carbohidratos bajos ({pct_hc}%)")
                if pct_hc > 70:    problemas.append(f"carbohidratos altos ({pct_hc}%)")
                if problemas:
                    eval_e, icon_e = f"Desequilibrio en: {', '.join(problemas)}.", "🟠"
                else:
                    eval_e, icon_e = f"Proporción adecuada — Prot: {pct_prot}% | Lip: {pct_lip}% | HC: {pct_hc}%.", "🟢"
            else:
                eval_e, icon_e = "Sin datos de macronutrientes.", "⬜"
            resultados["Equilibrada"] = (icon_e, eval_e)

            tiempos_registrados = set()
            for df_d in r24h_dias.values():
                if isinstance(df_d, pd.DataFrame) and not df_d.empty and "Tiempo" in df_d.columns:
                    tiempos_registrados.update(df_d["Tiempo"].unique())
            n_t = len(tiempos_registrados)
            if n_t == 0:      eval_s, icon_s = "Sin registros de tiempos de comida.", "⬜"
            elif n_t >= 4:    eval_s, icon_s = f"Suficientes tiempos de comida — {n_t} tiempos.", "🟢"
            elif n_t == 3:    eval_s, icon_s = f"Tiempos mínimos — {n_t} tiempos.", "🟡"
            else:             eval_s, icon_s = f"Insuficientes — solo {n_t} tiempo(s).", "🔴"
            resultados["Suficiente"] = (icon_s, eval_s)

            GRUPOS = {
                "Cereales/Tubérculos": ["ARROZ","AVENA","PAN","FIDEO","PAPA","MAIZ","QUINUA"],
                "Leguminosas": ["ARVEJA","LENTEJA","FRIJOL","HABA","GARBANZO","SOYA"],
                "Verduras": ["ZANAHORIA","TOMATE","LECHUGA","CEBOLLA","ESPINACA"],
                "Frutas": ["MANZANA","PLATANO","NARANJA","DURAZNO","PAPAYA"],
                "Carnes": ["POLLO","RES","CERDO","PESCADO","ATUN","HUEVO"],
                "Lácteos": ["LECHE","YOGUR","QUESO"],
                "Grasas/Aceites": ["ACEITE","MANTEQUILLA","MARGARINA"],
            }
            alimentos_c = set()
            for df_d in r24h_dias.values():
                if isinstance(df_d, pd.DataFrame) and not df_d.empty and "Alimento" in df_d.columns:
                    alimentos_c.update(df_d["Alimento"].str.upper().tolist())
            grupos_p = [g for g, items in GRUPOS.items() if any(any(i in a for i in items) for a in alimentos_c)]
            n_g = len(grupos_p)
            if n_g >= 6:    eval_v, icon_v = f"Consume alimentos de {n_g}/7 grupos.", "🟢"
            elif n_g >= 4:  eval_v, icon_v = f"Variedad moderada — {n_g}/7 grupos.", "🟡"
            else:           eval_v, icon_v = f"Poca variedad — solo {n_g}/7 grupos.", "🔴"
            resultados["Variada"] = (icon_v, eval_v)

            lugar = st.session_state.get("lugar_consumo", "")
            if "hospital" in lugar.lower() or "instituc" in lugar.lower():
                eval_i, icon_i = "Elaborada en institución con control sanitario.", "🟢"
            elif "casa" in lugar.lower():
                eval_i, icon_i = "Preparación en casa — inocuidad según hábitos del hogar.", "🟡"
            elif "calle" in lugar.lower() or "restaurante" in lugar.lower():
                eval_i, icon_i = "Fuera del hogar — mayor riesgo de contaminación.", "🟠"
            else:
                eval_i, icon_i = "Sin datos de lugar de preparación.", "⬜"
            resultados["Inocua"] = (icon_i, eval_i)

            dx_list = st.session_state.get("v_dx_multi", [])
            if dx_list:
                eval_ph, icon_ph = f"Debe adecuarse a: {', '.join(dx_list[:3])}.", "🟡"
            else:
                eval_ph, icon_ph = "Sin diagnósticos registrados.", "⬜"
            resultados["P.H."] = (icon_ph, eval_ph)
            return resultados

        evaluaciones = evaluar_dieta(prom_vn, macro_pta, macro_ptb, r24h_dias)
        for caract in ["Completa", "Equilibrada", "Suficiente", "Variada", "Inocua", "P.H."]:
            icon, texto_auto = evaluaciones.get(caract, ("⬜", "Sin datos."))
            with st.expander(f"{icon} {caract}", expanded=True):
                col_auto, col_edit = st.columns([1, 1])
                with col_auto:
                    st.markdown("**Evaluación automática:**")
                    st.info(texto_auto)
                with col_edit:
                    st.markdown("**Ajuste clínico (editable):**")
                    key_edit = f"analisis_dieta_{caract}"
                    if key_edit not in st.session_state:
                        st.session_state[key_edit] = texto_auto
                    texto_final = st.text_area("Modificar:", value=st.session_state[key_edit],
                                               height=80, key=f"ta_{caract}", label_visibility="collapsed")
                    st.session_state[key_edit] = texto_final

        st.session_state["analisis_dieta_final"] = {c: st.session_state.get(f"analisis_dieta_{c}", "") for c in ["Completa","Equilibrada","Suficiente","Variada","Inocua","P.H."]}

    # ================================================================
    # PESTAÑA 4 — DETERMINACIÓN DE NECESIDADES ENERGÉTICAS
    # ================================================================
    with tabs[3]:
        st.subheader("V. DETERMINACIÓN DE NECESIDADES ENERGÉTICAS")
        st.markdown("---")

        peso_lectura   = st.session_state.get("a_peso", 0.0)
        talla_lectura  = st.session_state.get("a_talla", 0.0)
        edad_lectura   = int(paciente.get("edad", st.session_state.get("f_edad", 0)))
        sexo_lectura   = paciente.get("sexo", st.session_state.get("f_sexo", "Femenino"))
        muñeca_lectura = st.session_state.get("a_circunferencia_muneca", 0.0)

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.text_input("Peso (kg)",      value=f"{peso_lectura}",   disabled=True, key="vn_lect_p")
        c2.text_input("Talla (m)",      value=f"{talla_lectura}",  disabled=True, key="vn_lect_t")
        c3.text_input("Edad",           value=f"{edad_lectura}",   disabled=True, key="vn_lect_e")
        c4.text_input("Sexo",           value=f"{sexo_lectura}",   disabled=True, key="vn_lect_s")
        c5.text_input("C. Muñeca (cm)", value=f"{muñeca_lectura}", disabled=True, key="vn_lect_m")
        st.markdown("---")

        formula_opciones = ["Harris-Benedict (1919)", "Mifflin-St Jeor", "OMS / FAO / UNU", "Valencia", "Roza y Shizgal (1984)"]
        seleccion_formula = st.selectbox("Seleccione Fórmula para TMB/GER:", options=formula_opciones, key="selector_tmb_principal")
        st.markdown("---")

        # A. Peso Teórico
        st.subheader("A. Peso Teórico o Peso Ideal")
        metodo_pi = st.selectbox("Método para determinar Peso Ideal:",
            ["Complexión Física (Índice R)", "IMC Estándar (OMS)", "Fórmula de Hamwi"],
            key="metodo_peso_ideal_selector")

        peso_ideal_final = 0.0
        es_adulto_mayor  = edad_lectura >= 65
        imc_p, imc_m, imc_g = (20.0, 22.0, 24.0) if not es_adulto_mayor else (23.0, 25.0, 27.0)

        if metodo_pi == "Complexión Física (Índice R)":
            if talla_lectura > 0 and muñeca_lectura > 0:
                r_val = (talla_lectura * 100) / muñeca_lectura
                if sexo_lectura == "Masculino":
                    imc_target = imc_p if r_val > 10.4 else (imc_g if r_val < 9.6 else imc_m)
                else:
                    imc_target = imc_p if r_val > 11.0 else (imc_g if r_val < 10.1 else imc_m)
                peso_ideal_final = imc_target * (talla_lectura ** 2)
            else:
                st.warning("⚠️ Faltan datos (Talla o Muñeca) para calcular.")
        elif metodo_pi == "IMC Estándar (OMS)":
            imc_fijo = 22.0 if not es_adulto_mayor else 25.0
            peso_ideal_final = imc_fijo * (talla_lectura ** 2)
        elif metodo_pi == "Fórmula de Hamwi":
            talla_cm = talla_lectura * 100
            if talla_cm > 152.4:
                p_extra = (talla_cm - 152.4) / 2.54
                base = 48.0 if sexo_lectura == "Masculino" else 45.5
                mult = 2.7  if sexo_lectura == "Masculino" else 2.2
                peso_ideal_final = base + (mult * p_extra)
            else:
                peso_ideal_final = 48.0 if sexo_lectura == "Masculino" else 45.5

        st.success(f"### Peso Ideal Calculado: {peso_ideal_final:.2f} kg")
        st.info(f"### **{seleccion_formula}**")
        st.session_state["v_peso_ideal_calculado"] = peso_ideal_final

        if peso_ideal_final > 0 and talla_lectura > 0 and edad_lectura > 0:
            st.markdown("---")
            bloque_calculo_energetico(
                label="A. Para el Peso Teórico",
                peso=peso_ideal_final, talla=talla_lectura,
                edad=edad_lectura, sexo=sexo_lectura,
                formula=seleccion_formula, key_prefix="pta"
            )
        elif talla_lectura == 0 or peso_lectura == 0:
            st.info("💡 Ingrese y guarde los datos en Antropometría y Filiación para ver el cálculo.")

        # B. Peso Actual
        if peso_lectura > 0 and talla_lectura > 0 and edad_lectura > 0:
            st.markdown("---")
            st.subheader("B. Para el Peso Actual")
            if peso_ideal_final > 0:
                diff = peso_lectura - peso_ideal_final
                if abs(diff) < 0.5:
                    st.success("✅ El peso actual coincide con el peso ideal.")
                elif diff > 0:
                    st.warning(f"⚠️ Exceso de peso: +{diff:.2f} kg sobre el peso ideal ({peso_ideal_final:.2f} kg)")
                else:
                    st.warning(f"⚠️ Déficit de peso: {diff:.2f} kg bajo el peso ideal ({peso_ideal_final:.2f} kg)")
            st.markdown("---")
            bloque_calculo_energetico(
                label="B. Para el Peso Actual",
                peso=peso_lectura, talla=talla_lectura,
                edad=edad_lectura, sexo=sexo_lectura,
                formula=seleccion_formula, key_prefix="ptb"
            )

    # ================================================================
    # PESTAÑA 5 — INDICADORES BIOQUÍMICOS
    # ================================================================
    with tabs[4]:
        st.subheader("VI. ANÁLISIS DE INDICADORES BIOQUÍMICOS")
        st.markdown("---")

        df_bio = st.session_state.get("datos_bioquimicos", pd.DataFrame())

        if df_bio.empty:
            st.info("💡 Ingrese y guarde los datos en Recolección → Bioquímico.")
        else:
            def get_bio(nombre):
                try:
                    val = float(df_bio.loc[df_bio["Parámetro"] == nombre, "Valor"].values[0])
                    return val if val > 0 else None
                except: return None

            albumina  = get_bio("Albúmina")
            prealbum  = get_bio("Prealbúmina")
            pcr       = get_bio("Proteína C Reactiva (PCR)")
            linfos    = get_bio("Linfocitos Totales")
            glucosa   = get_bio("Glucosa")
            creatinin = get_bio("Creatinina")
            urea      = get_bio("Urea")
            hemoglob  = get_bio("Hemoglobina")
            sexo_b    = paciente.get("sexo", st.session_state.get("f_sexo", "Masculino"))

            def interpretar(param, valor, ref_min, ref_max, unidad,
                            interp_bajo, interp_normal, interp_alto, imp_bajo="", imp_alto=""):
                if valor is None: return None
                if valor < ref_min:
                    estado, interp, imp = "🔴 Bajo", interp_bajo, imp_bajo
                elif valor > ref_max:
                    estado, interp, imp = "🟠 Alto", interp_alto, imp_alto
                else:
                    estado, interp, imp = "🟢 Normal", interp_normal, ""
                return {"Parámetro": param, "Valor": f"{valor} {unidad}",
                        "Referencia": f"{ref_min} - {ref_max} {unidad}",
                        "Estado": estado, "Interpretación clínica": interp,
                        "Implicancia nutricional": imp}

            resultados = []

            if albumina is not None:
                if albumina < 3.5:
                    if pcr and pcr > 10:
                        interp_alb = f"Hipoalbuminemia por inflamación activa (PCR: {pcr} mg/L)."
                        imp_alb    = "No restringir proteínas. Tratar inflamación. Aportar aa ramificados."
                    else:
                        interp_alb = "Hipoalbuminemia por desnutrición proteico-energética crónica."
                        imp_alb    = "Aumentar aporte proteico de alto VB. Meta: >3.5 g/dL."
                    resultados.append({"Parámetro": "Albúmina", "Valor": f"{albumina} g/dL",
                                       "Referencia": "3.5 - 5.0 g/dL", "Estado": "🔴 Bajo",
                                       "Interpretación clínica": interp_alb, "Implicancia nutricional": imp_alb})
                else:
                    resultados.append({"Parámetro": "Albúmina", "Valor": f"{albumina} g/dL",
                                       "Referencia": "3.5 - 5.0 g/dL", "Estado": "🟢 Normal",
                                       "Interpretación clínica": "Estado proteico visceral adecuado.", "Implicancia nutricional": ""})

            r = interpretar("Prealbúmina", prealbum, 15, 35, "mg/dL",
                "Depleción proteica reciente.", "Estado proteico agudo adecuado.", "Posible deshidratación.",
                imp_bajo="Incrementar proteínas de alto VB.")
            if r: resultados.append(r)

            r = interpretar("PCR", pcr, 0, 10, "mg/L", "", "Sin proceso inflamatorio activo.",
                "Inflamación activa presente.", imp_alto="Priorizar antiinflamatorios dietéticos (Omega-3).")
            if r: resultados.append(r)

            if linfos is not None:
                if linfos < 1500:
                    interp_l = "Linfocitopenia severa." if linfos < 900 else ("Linfocitopenia moderada." if linfos < 1200 else "Linfocitopenia leve.")
                    imp_l    = "Dieta inmunomoduladora: Zinc, Vit. C, Vit. A, Selenio."
                    resultados.append({"Parámetro": "Linfocitos Totales", "Valor": f"{linfos} mm³",
                                       "Referencia": "1500 - 4000 mm³", "Estado": "🔴 Bajo",
                                       "Interpretación clínica": interp_l, "Implicancia nutricional": imp_l})
                else:
                    resultados.append({"Parámetro": "Linfocitos Totales", "Valor": f"{linfos} mm³",
                                       "Referencia": "1500 - 4000 mm³", "Estado": "🟢 Normal",
                                       "Interpretación clínica": "Inmunocompetencia conservada.", "Implicancia nutricional": ""})

            r = interpretar("Glucosa", glucosa, 70, 100, "mg/dL",
                "Hipoglucemia.", "Glucemia en ayunas normal.", "Hiperglucemia en ayunas.",
                imp_bajo="Fraccionamiento de comidas. Carbohidratos complejos.",
                imp_alto="Control de carga glucémica. Aumentar fibra.")
            if r: resultados.append(r)

            ref_cre_max = 1.2 if sexo_b == "Masculino" else 1.1
            r = interpretar("Creatinina", creatinin, 0.7, ref_cre_max, "mg/dL",
                "Posible desnutrición muscular.", "Función renal conservada.", "Posible insuficiencia renal.",
                imp_bajo="Evaluar masa muscular.", imp_alto="Restricción proteica según TFG.")
            if r: resultados.append(r)

            r = interpretar("Urea", urea, 15, 45, "mg/dL",
                "Posible baja ingesta proteica.", "Metabolismo proteico adecuado.", "Posible exceso proteico.",
                imp_bajo="Evaluar aporte proteico.", imp_alto="Revisar hidratación y función renal.")
            if r: resultados.append(r)

            ref_hb_min = 13.0 if sexo_b == "Masculino" else 12.0
            ref_hb_max = 17.5 if sexo_b == "Masculino" else 15.5
            if hemoglob is not None:
                if hemoglob < ref_hb_min:
                    interp_hb = "Anemia severa." if hemoglob < (ref_hb_min - 3) else "Anemia leve-moderada."
                    imp_hb    = "Hierro hemínico prioritario + Vit. C. Evitar taninos."
                    resultados.append({"Parámetro": "Hemoglobina", "Valor": f"{hemoglob} g/dL",
                                       "Referencia": f"{ref_hb_min} - {ref_hb_max} g/dL",
                                       "Estado": "🔴 Bajo", "Interpretación clínica": interp_hb,
                                       "Implicancia nutricional": imp_hb})
                else:
                    resultados.append({"Parámetro": "Hemoglobina", "Valor": f"{hemoglob} g/dL",
                                       "Referencia": f"{ref_hb_min} - {ref_hb_max} g/dL",
                                       "Estado": "🟢 Normal", "Interpretación clínica": "Transporte de oxígeno adecuado.", "Implicancia nutricional": ""})

            if resultados:
                st.dataframe(pd.DataFrame(resultados), use_container_width=True, hide_index=True)
                alertas = [r for r in resultados if "🔴" in r["Estado"] or "🟠" in r["Estado"]]
                if alertas:
                    st.markdown("#### 🚨 Alertas prioritarias")
                    for a in alertas:
                        st.error(f"**{a['Parámetro']}** ({a['Valor']}) — {a['Interpretación clínica']}")
                        if a['Implicancia nutricional']:
                            st.info(f"➡️ {a['Implicancia nutricional']}")
                else:
                    st.success("✅ Todos los parámetros bioquímicos dentro de rangos normales.")
                st.session_state["eval_bioquimica"] = resultados

    # ================================================================
    # PESTAÑA 6 — EVALUACIÓN ANTROPOMÉTRICA
    # ================================================================
    with tabs[5]:
        st.subheader("VII. EVALUACIÓN ANTROPOMÉTRICA")
        st.markdown("---")

        peso    = st.session_state.get("a_peso", 0.0)
        talla   = st.session_state.get("a_talla", 0.0)
        muneca  = st.session_state.get("a_circunferencia_muneca", 0.0)
        cintura = st.session_state.get("a_circ_cintura", 0.0)
        cadera  = st.session_state.get("a_circ_cadera", 0.0)
        brazo   = st.session_state.get("a_circ_brazo", 0.0)
        sexo_a  = paciente.get("sexo", st.session_state.get("f_sexo", "Masculino"))
        edad_a  = int(paciente.get("edad", st.session_state.get("f_edad", 30)))
        datos_antro = st.session_state.get("datos_antropo", pd.DataFrame())

        def get_dato(df, nombre):
            try: return float(df.loc[df["Determinación"] == nombre, "Dato"].values[0])
            except: return 0.0

        pli_tri = get_dato(datos_antro, "Pliegue cutáneo tricipital")
        pli_bic = get_dato(datos_antro, "Pliegue cutáneo bicipital")
        pli_sub = get_dato(datos_antro, "Pliegue cutáneo subescapular")
        pli_sup = get_dato(datos_antro, "Pliegue cutáneo suprailiaco")

        if peso == 0 or talla == 0:
            st.warning("⚠️ Ingrese y guarde los datos antropométricos primero.")
        else:
            # Complexión
            st.subheader("1. Complexión Física")
            if muneca > 0:
                r_val = (talla * 100) / muneca
                if sexo_a == "Masculino":
                    complexion = "Pequeña" if r_val > 10.4 else ("Grande" if r_val < 9.6 else "Mediana")
                else:
                    complexion = "Pequeña" if r_val > 11.0 else ("Grande" if r_val < 10.1 else "Mediana")
                c1, c2, c3 = st.columns(3)
                c1.metric("Índice R", f"{r_val:.2f}")
                c2.metric("Complexión", complexion)
                c3.metric("Talla / Muñeca", f"{talla*100:.1f} / {muneca:.1f} cm")
            else:
                st.info("Ingrese circunferencia de muñeca para calcular complexión.")
                complexion = "No calculada"; r_val = 0.0

            st.markdown("---")
            st.subheader("2. Índice de Masa Corporal (IMC)")
            imc = peso / (talla ** 2)
            if edad_a >= 65:
                clasif_imc = "Bajo peso (adulto mayor)" if imc < 22 else ("Normal (adulto mayor)" if imc < 27 else ("Sobrepeso (adulto mayor)" if imc < 30 else "Obesidad (adulto mayor)"))
            else:
                if imc < 16: clasif_imc = "Desnutrición severa"
                elif imc < 17: clasif_imc = "Desnutrición moderada"
                elif imc < 18.5: clasif_imc = "Bajo peso"
                elif imc < 25: clasif_imc = "Normal"
                elif imc < 30: clasif_imc = "Sobrepeso"
                elif imc < 35: clasif_imc = "Obesidad grado I"
                elif imc < 40: clasif_imc = "Obesidad grado II"
                else: clasif_imc = "Obesidad grado III"
            c1, c2 = st.columns(2)
            c1.metric("IMC", f"{imc:.2f} kg/m²")
            c2.metric("Clasificación OMS", clasif_imc)

            st.markdown("---")
            st.subheader("3. Composición Corporal")
            suma_pliegues = pli_tri + pli_bic + pli_sub + pli_sup

            if suma_pliegues > 0:
                import math
                log_sp = math.log10(suma_pliegues)
                if sexo_a == "Masculino":
                    if edad_a < 17:    dc = 1.1533 - (0.0643 * log_sp)
                    elif edad_a < 20:  dc = 1.1620 - (0.0630 * log_sp)
                    elif edad_a < 30:  dc = 1.1631 - (0.0632 * log_sp)
                    elif edad_a < 40:  dc = 1.1422 - (0.0544 * log_sp)
                    elif edad_a < 50:  dc = 1.1620 - (0.0700 * log_sp)
                    else:              dc = 1.1715 - (0.0779 * log_sp)
                else:
                    if edad_a < 17:    dc = 1.1369 - (0.0598 * log_sp)
                    elif edad_a < 20:  dc = 1.1549 - (0.0678 * log_sp)
                    elif edad_a < 30:  dc = 1.1599 - (0.0717 * log_sp)
                    elif edad_a < 40:  dc = 1.1423 - (0.0632 * log_sp)
                    elif edad_a < 50:  dc = 1.1333 - (0.0612 * log_sp)
                    else:              dc = 1.1339 - (0.0645 * log_sp)

                pct_grasa = ((4.95 / dc) - 4.50) * 100
                if sexo_a == "Masculino":
                    rango_n = (8,20) if edad_a < 40 else ((11,22) if edad_a < 60 else (13,25))
                else:
                    rango_n = (21,33) if edad_a < 40 else ((23,35) if edad_a < 60 else (24,36))

                if pct_grasa < rango_n[0]:      clasif_grasa = "🔵 Bajo en grasa"
                elif pct_grasa <= rango_n[1]:   clasif_grasa = "🟢 Normal"
                elif pct_grasa <= rango_n[1]+5: clasif_grasa = "🟠 Elevado"
                else:                            clasif_grasa = "🔴 Obesidad"

                grasa_total_kg  = round((pct_grasa / 100) * peso, 2)
                mlg_kg          = round(peso - grasa_total_kg, 2)
                pct_grasa_ideal = (rango_n[0] + rango_n[1]) / 2
                exceso_grasa_kg = round(grasa_total_kg - round((pct_grasa_ideal/100)*peso,2), 2)
                exceso_pct      = round(pct_grasa - pct_grasa_ideal, 1)

                masa_muscular = None
                if brazo > 0 and pli_tri > 0:
                    cmc = brazo - (3.14159 * (pli_tri / 10))
                    masa_muscular = round((0.0264 + (0.0029 * (peso * cmc))), 2) if sexo_a == "Masculino" \
                        else round((0.0264 + (0.0029 * (peso * cmc * 0.88))), 2)

                agua_total = round(-2.097 + (0.1069 * talla * 100) + (0.2466 * peso), 2) if sexo_a == "Masculino" \
                    else round(-2.097 + (0.1069 * talla * 100) + (0.1835 * peso), 2)

                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Suma pliegues", f"{suma_pliegues:.1f} mm")
                c2.metric("Densidad corporal", f"{dc:.4f} g/cc")
                c3.metric("% Grasa corporal", f"{pct_grasa:.1f}%")
                c4.metric("Estado", clasif_grasa)

                st.dataframe(pd.DataFrame([
                    {"Parámetro": "% Grasa corporal",            "Valor": f"{pct_grasa:.1f}%",     "Interpretación": clasif_grasa},
                    {"Parámetro": "Grasa corporal total",         "Valor": f"{grasa_total_kg} kg",  "Interpretación": f"Rango normal: {rango_n[0]}-{rango_n[1]}%"},
                    {"Parámetro": "Masa libre de grasa",          "Valor": f"{mlg_kg} kg",           "Interpretación": "Músculo + hueso + agua + vísceras"},
                    {"Parámetro": "% Exceso/déficit grasa",       "Valor": f"{exceso_pct:+.1f}%",   "Interpretación": "🟢 Normal" if abs(exceso_pct) < 3 else ("🔴 Exceso" if exceso_pct > 0 else "🔵 Déficit")},
                    {"Parámetro": "Masa muscular estimada",       "Valor": f"{masa_muscular} kg" if masa_muscular else "Sin datos", "Interpretación": "Fórmula Heymsfield"},
                    {"Parámetro": "Agua corporal total",          "Valor": f"{agua_total} L",        "Interpretación": "Fórmula Watson"},
                ]), use_container_width=True, hide_index=True)

                if cintura > 0 and cadera > 0:
                    st.markdown("---")
                    st.subheader("4. Riesgo Cardiovascular")
                    icc = cintura / cadera
                    if sexo_a == "Masculino":
                        riesgo_icc = "🔴 Alto riesgo" if icc > 1.0 else ("🟠 Moderado" if icc > 0.95 else "🟢 Normal")
                    else:
                        riesgo_icc = "🔴 Alto riesgo" if icc > 0.85 else ("🟠 Moderado" if icc > 0.80 else "🟢 Normal")
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Cintura", f"{cintura} cm")
                    c2.metric("Cadera", f"{cadera} cm")
                    c3.metric("ICC", f"{icc:.2f}")
                    c4.metric("Riesgo CV", riesgo_icc)
                    if sexo_a == "Masculino":
                        riesgo_cin = "🔴 Riesgo muy alto" if cintura > 102 else ("🟠 Riesgo aumentado" if cintura > 94 else "🟢 Normal")
                    else:
                        riesgo_cin = "🔴 Riesgo muy alto" if cintura > 88 else ("🟠 Riesgo aumentado" if cintura > 80 else "🟢 Normal")
                    st.info(f"Riesgo por cintura sola: {riesgo_cin}")

                st.session_state["eval_antro"] = {
                    "imc": round(imc, 2), "clasif_imc": clasif_imc,
                    "complexion": complexion, "r_val": round(r_val, 2),
                    "pct_grasa": round(pct_grasa, 1), "clasif_grasa": clasif_grasa,
                    "grasa_total_kg": grasa_total_kg, "mlg_kg": mlg_kg,
                    "masa_muscular": masa_muscular, "agua_total": agua_total,
                }
            else:
                st.info("💡 Ingrese los 4 pliegues cutáneos para calcular composición corporal completa.")
                c1, c2 = st.columns(2)
                c1.metric("IMC", f"{imc:.2f} kg/m²")
                c2.metric("Clasificación", clasif_imc)
                if cintura > 0 and cadera > 0:
                    icc = cintura / cadera
                    riesgo_icc = ("🔴 Alto" if icc > 1.0 else ("🟠 Moderado" if icc > 0.95 else "🟢 Normal")) if sexo_a == "Masculino" \
                        else ("🔴 Alto" if icc > 0.85 else ("🟠 Moderado" if icc > 0.80 else "🟢 Normal"))
                    c1.metric("ICC", f"{icc:.2f}")
                    c2.metric("Riesgo CV", riesgo_icc)

    # ================================================================
    # PESTAÑA 7 — EVALUACIÓN DEL C.A.P.
    # ================================================================
    with tabs[6]:
        st.subheader("VIII. EVALUACIÓN DEL C.A.P. ALIMENTARIO NUTRICIONAL")
        st.markdown("---")

        perfil    = st.session_state.get("perfil_psico", {})
        cap_c     = perfil.get("cap_conocimiento", None)
        cap_a     = perfil.get("cap_aptitud", None)
        cap_p     = perfil.get("cap_practica", None)
        recursos  = perfil.get("recursos", None)
        religion  = perfil.get("religion", None)
        sustancias= perfil.get("sustancias", [])
        educacion = perfil.get("educacion", None)

        if not cap_c:
            st.info("💡 Complete la sección Psicosocial en Recolección de Datos.")
        else:
            puntaje_c = {"Bajo": 1, "Medio": 2, "Alto": 3}.get(cap_c, 0)
            puntaje_a = {"Baja": 1, "Media": 2, "Alta": 3}.get(cap_a, 0)
            puntaje_p = {"Deficiente": 1, "Regular": 2, "Buena": 3}.get(cap_p, 0)
            puntaje_total = puntaje_c + puntaje_a + puntaje_p

            ico_c = "🔴" if puntaje_c == 1 else ("🟡" if puntaje_c == 2 else "🟢")
            ico_a = "🔴" if puntaje_a == 1 else ("🟡" if puntaje_a == 2 else "🟢")
            ico_p = "🔴" if puntaje_p == 1 else ("🟡" if puntaje_p == 2 else "🟢")

            interp_c = {"Bajo": "Desconoce conceptos básicos de nutrición.", "Medio": "Tiene nociones generales con vacíos importantes.", "Alto": "Comprende adecuadamente la alimentación saludable."}
            interp_a = {"Baja": "No muestra disposición para cambiar hábitos.", "Media": "Muestra interés limitado en mejorar su alimentación.", "Alta": "Predispuesto y motivado para adoptar cambios."}
            interp_p = {"Deficiente": "Sus prácticas alimentarias representan riesgo nutricional.", "Regular": "Prácticas parcialmente adecuadas con aspectos a mejorar.", "Buena": "Aplica correctamente los conocimientos en su alimentación."}
            recom_c  = {"Bajo": "Educación nutricional básica: grupos alimentarios, porciones.", "Medio": "Reforzar conceptos de equilibrio dietético.", "Alto": "Profundizar en nutrición terapéutica según patología."}
            recom_a  = {"Baja": "Trabajo motivacional. Identificar barreras y metas pequeñas.", "Media": "Fortalecer motivación con resultados tangibles.", "Alta": "Aprovechar disposición para implementar cambios profundos."}
            recom_p  = {"Deficiente": "Intervención urgente. Guías prácticas simples.", "Regular": "Corrección de prácticas específicas. Menú modelo semanal.", "Buena": "Mantener y optimizar. Ajustes finos según requerimientos."}

            df_cap = pd.DataFrame([
                {"Dimensión": f"{ico_c} Conocimientos", "Nivel": cap_c, "Interpretación": interp_c[cap_c], "Recomendación": recom_c[cap_c]},
                {"Dimensión": f"{ico_a} Actitudes",     "Nivel": cap_a, "Interpretación": interp_a[cap_a], "Recomendación": recom_a[cap_a]},
                {"Dimensión": f"{ico_p} Prácticas",     "Nivel": cap_p, "Interpretación": interp_p[cap_p], "Recomendación": recom_p[cap_p]},
            ])
            st.dataframe(df_cap, use_container_width=True, hide_index=True)

            st.markdown("---")
            c1, c2, c3 = st.columns(3)
            c1.metric("Puntaje CAP", f"{puntaje_total}/9")

            if puntaje_total <= 3:
                nivel_cap, concl_cap = "🔴 CAP Deficiente", "Requiere intervención educativa intensiva y seguimiento frecuente."
            elif puntaje_total <= 6:
                nivel_cap, concl_cap = "🟡 CAP Regular", "Intervención educativa dirigida a las dimensiones más débiles."
            else:
                nivel_cap, concl_cap = "🟢 CAP Adecuado", "Refuerzo positivo y educación de mantenimiento."

            c2.metric("Nivel global", nivel_cap)
            c3.metric("Educación", educacion or "No registrado")
            st.info(f"**Conclusión:** {concl_cap}")

            st.markdown("---")
            st.subheader("Factores Condicionantes")
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**Recursos económicos:**")
                rec_ico = {"Muy limitada": "🔴", "Limitada": "🟠", "Suficiente": "🟢", "Holgada": "🟢"}.get(recursos, "⬜")
                rec_imp = {
                    "Muy limitada": "Limitación severa. Priorizar alimentos económicos y nutritivos.",
                    "Limitada":     "Restricción presupuestaria. Orientar hacia opciones de bajo costo.",
                    "Suficiente":   "Capacidad adecuada para seguir la dieta prescrita.",
                    "Holgada":      "Sin barreras económicas. Mayor flexibilidad en la prescripción."
                }.get(recursos, "")
                st.write(f"{rec_ico} **{recursos}** — {rec_imp}")
            with c2:
                st.markdown("**Sustancias nocivas:**")
                if sustancias and "Ninguno" not in sustancias:
                    for s in sustancias:
                        imp_s = {
                            "Tabaco":            "🚬 Aumenta requerimiento de Vit. C. Favorece estrés oxidativo.",
                            "Alcohol":           "🍺 Depleta B1, B6, B12, folato, Zinc y Magnesio.",
                            "Drogas recreativas":"💊 Altera apetito y metabolismo."
                        }.get(s, "")
                        st.warning(imp_s)
                else:
                    st.success("✅ Sin consumo de sustancias nocivas reportado.")

            if religion:
                imp_rel = {
                    "Adventista":         "⚠️ Posible dieta vegetariana — vigilar B12, Hierro y Zinc.",
                    "Testigos de Jehová": "⚠️ Rechazo a transfusiones — monitorear Hemoglobina.",
                    "Católica":           "✅ Sin restricciones dietéticas de relevancia clínica.",
                }.get(religion, "")
                if imp_rel:
                    st.info(f"**Consideración religiosa ({religion}):** {imp_rel}")

            st.session_state["eval_cap"] = {
                "conocimiento": cap_c, "actitud": cap_a, "practica": cap_p,
                "puntaje": puntaje_total, "nivel": nivel_cap,
                "conclusion": concl_cap, "recursos": recursos
            }

    # ================================================================
    # PESTAÑA 8 — DIAGNÓSTICO FINAL NUTRICIONAL
    # ================================================================
    with tabs[7]:
        st.subheader("IX. DIAGNÓSTICO NUTRICIONAL FINAL")
        st.markdown("---")

        eval_antro  = st.session_state.get("eval_antro", {})
        eval_bio    = st.session_state.get("eval_bioquimica", [])
        eval_cap    = st.session_state.get("eval_cap", {})
        prom_r24    = st.session_state.get("r24h_promedio", {})
        macro_pta   = st.session_state.get("macro_pta", {})
        dx_medicos  = st.session_state.get("v_dx_multi", [])

        # Panel resumen
        st.subheader("Resumen Integrado")
        col1, col2, col3, col4 = st.columns(4)

        imc_dx    = eval_antro.get("imc", 0)
        clasif_dx = eval_antro.get("clasif_imc", "Sin datos")
        col1.metric("IMC", f"{imc_dx} kg/m²" if imc_dx else "Sin datos", clasif_dx)

        pct_g_dx    = eval_antro.get("pct_grasa", 0)
        clasif_g_dx = eval_antro.get("clasif_grasa", "Sin datos")
        col2.metric("% Grasa", f"{pct_g_dx}%" if pct_g_dx else "Sin datos", clasif_g_dx)

        cap_nivel = eval_cap.get("nivel", "Sin datos")
        cap_punt  = eval_cap.get("puntaje", 0)
        col3.metric("CAP", cap_nivel if cap_nivel else "Sin datos", f"{cap_punt}/9 puntos" if cap_punt else "")

        kcal_prom = prom_r24.get("Energia", 0)
        req_kcal  = macro_pta.get("total_kcal", 0)
        if kcal_prom > 0 and req_kcal > 0:
            pct_adec = round((kcal_prom / req_kcal) * 100, 1)
            col4.metric("Adec. Calórica", f"{pct_adec}%",
                        "✅ Adecuado" if 90 <= pct_adec <= 110 else ("🔴 Insuficiente" if pct_adec < 90 else "🟠 Excesivo"))
        else:
            pct_adec = 0
            col4.metric("Adec. Calórica", "Sin datos")

        st.markdown("---")

        # Diagnóstico automático
        st.subheader("Diagnóstico Automático Generado")
        partes_dx = []
        if clasif_dx and clasif_dx != "Sin datos":
            partes_dx.append(f"Paciente con **{clasif_dx}** según IMC ({imc_dx} kg/m²)")
        if pct_g_dx:
            partes_dx.append(f"con **{clasif_g_dx.replace('🟢','').replace('🔴','').replace('🟠','').strip()}** en porcentaje de grasa corporal ({pct_g_dx}%)")
        bio_alb = next((b for b in eval_bio if b["Parámetro"] == "Albúmina"), None)
        if bio_alb:
            if "🔴" in bio_alb["Estado"]:
                partes_dx.append(f"con **depleción proteica visceral** (Albúmina: {bio_alb['Valor']})")
            else:
                partes_dx.append("con **estado proteico conservado**")
        bio_hb = next((b for b in eval_bio if b["Parámetro"] == "Hemoglobina"), None)
        if bio_hb and "🔴" in bio_hb["Estado"]:
            partes_dx.append(f"asociado a **anemia** (Hb: {bio_hb['Valor']})")
        if kcal_prom > 0 and req_kcal > 0:
            if pct_adec < 90:
                partes_dx.append(f"con **ingesta calórica insuficiente** ({pct_adec}% del requerimiento)")
            elif pct_adec > 110:
                partes_dx.append(f"con **ingesta calórica excesiva** ({pct_adec}% del requerimiento)")
            else:
                partes_dx.append(f"con **ingesta calórica adecuada** ({pct_adec}%)")
        if cap_nivel and "Sin datos" not in cap_nivel:
            nivel_simple = cap_nivel.replace("🔴","").replace("🟡","").replace("🟢","").strip()
            partes_dx.append(f"y **{nivel_simple}** en conocimientos, actitudes y prácticas alimentarias")
        if dx_medicos:
            partes_dx.append(f"en contexto de: {', '.join(dx_medicos[:3])}{'...' if len(dx_medicos)>3 else ''}")

        if partes_dx:
            texto_auto_dx = ", ".join(partes_dx) + "."
            texto_auto_dx = texto_auto_dx[0].upper() + texto_auto_dx[1:]
        else:
            texto_auto_dx = "Complete las secciones de evaluación para generar el diagnóstico automático."

        st.info(f"**Diagnóstico sugerido:**\n\n{texto_auto_dx}")
        st.markdown("---")

        st.markdown("**Diagnóstico Nutricional Final (editable):**")
        st.caption("El sistema generó el texto base. Ajuste según su criterio clínico.")
        if "dx_nutricional_final" not in st.session_state:
            st.session_state["dx_nutricional_final"] = texto_auto_dx
        dx_final = st.text_area("Diagnóstico:", value=st.session_state["dx_nutricional_final"],
                                height=120, key="ta_dx_final", label_visibility="collapsed")
        st.session_state["dx_nutricional_final"] = dx_final

        st.markdown("---")

        # Objetivos nutricionales
        st.subheader("Objetivos Nutricionales")
        objetivos_opciones = [
            "Recuperar el estado nutricional", "Mantener el peso corporal actual",
            "Reducir peso corporal gradualmente", "Incrementar masa muscular",
            "Incrementar aporte de hierro", "Incrementar aporte de calcio",
            "Incrementar aporte de Vitamina C", "Incrementar aporte de Vitamina B12",
            "Controlar la carga glucémica", "Reducir consumo de sodio",
            "Reducir consumo de grasas saturadas", "Reducir consumo de azúcares simples",
            "Aumentar consumo de fibra dietética", "Mejorar fraccionamiento de comidas",
            "Adecuar textura de alimentos", "Evitar alimentos estimulantes",
            "Evitar alimentos ácidos", "Incrementar hidratación",
            "Educación nutricional al paciente", "Educación nutricional al cuidador/familia",
        ]

        objetivos_sugeridos = []
        if bio_hb and "🔴" in bio_hb["Estado"]:
            objetivos_sugeridos += ["Incrementar aporte de hierro", "Incrementar aporte de Vitamina C"]
        if bio_alb and "🔴" in bio_alb["Estado"]:
            objetivos_sugeridos.append("Recuperar el estado nutricional")
        if imc_dx and imc_dx < 18.5:
            objetivos_sugeridos.append("Recuperar el estado nutricional")
        if imc_dx and imc_dx >= 25:
            objetivos_sugeridos.append("Reducir peso corporal gradualmente")
        if imc_dx and imc_dx >= 30:
            objetivos_sugeridos.append("Reducir consumo de grasas saturadas")
        if cap_punt and cap_punt <= 6:
            objetivos_sugeridos.append("Educación nutricional al paciente")
        if kcal_prom and req_kcal and pct_adec < 90:
            objetivos_sugeridos.append("Mejorar fraccionamiento de comidas")
        for dx in dx_medicos:
            if "Diabetes" in dx or "Glucosa" in dx:
                objetivos_sugeridos.append("Controlar la carga glucémica")
            if "Hipertensión" in dx or "Renal" in dx:
                objetivos_sugeridos.append("Reducir consumo de sodio")
            if "Anemia" in dx:
                objetivos_sugeridos += ["Incrementar aporte de hierro", "Incrementar aporte de Vitamina C"]
        objetivos_sugeridos = list(dict.fromkeys(objetivos_sugeridos))

        if objetivos_sugeridos:
            st.success(f"✅ Objetivos sugeridos: {', '.join(objetivos_sugeridos)}")

        objetivos_seleccionados = st.multiselect("Seleccione objetivos:", objetivos_opciones,
            default=[o for o in objetivos_sugeridos if o in objetivos_opciones], key="objetivos_nutricionales")
        obj_extra = st.text_input("Objetivo adicional específico:", key="objetivo_extra",
                                   placeholder="Ej: Restricción de fósforo según estadio ERC")
        st.session_state["objetivos_finales"] = objetivos_seleccionados
        if obj_extra:
            st.session_state["objetivos_finales"].append(obj_extra)

        st.markdown("---")

        # Prescripción dietética
        st.subheader("Prescripción Dietética")
        c1, c2 = st.columns(2)
        with c1:
            tipo_dieta = st.multiselect("Tipo de dieta:",
                ["Dieta corriente", "Dieta blanda", "Dieta líquida",
                 "Dieta hipocalórica", "Dieta hipercalórica", "Dieta hiposódica",
                 "Dieta hiperproteica", "Dieta hipoproteica", "Dieta sin gluten",
                 "Dieta para diabético", "Dieta renal", "Dieta para dislipidemia",
                 "Dieta vegetariana", "Nutrición enteral", "Nutrición parenteral"],
                key="tipo_dieta")
        with c2:
            via_admin = st.selectbox("Vía de administración:",
                ["Vía oral", "Sonda nasogástrica", "Sonda nasoyeyunal",
                 "Gastrostomía", "Yeyunostomía",
                 "Nutrición parenteral central", "Nutrición parenteral periférica"],
                key="via_administracion")

        st.session_state["prescripcion_dietetica"] = {
            "diagnostico_final": dx_final,
            "objetivos": st.session_state.get("objetivos_finales", []),
            "tipo_dieta": tipo_dieta,
            "via_administracion": via_admin
        }

        if st.button("💾 Guardar Diagnóstico y Prescripción", type="primary", key="btn_save_dx"):
            st.success("✅ Diagnóstico nutricional y prescripción guardados correctamente.")
            st.balloons()

        st.markdown("---")

        # Dieta coordinada multi-patología
        st.subheader("X. PRESCRIPCIÓN DIETÉTICA — DIETA COORDINADA")
        st.markdown("---")

        @st.cache_data
        def cargar_dietas_patologias():
            ruta = "dietas_patologias.json"
            if os.path.exists(ruta):
                try:
                    with open(ruta, "r", encoding="utf-8") as f: return json.load(f)
                except: return {}
            return {}

        dietas_db = cargar_dietas_patologias()
        dx_list   = st.session_state.get("v_dx_multi", [])

        if not dx_list:
            st.info("💡 Registre los diagnósticos médicos en Recolección → Médicos.")
        elif not dietas_db:
            st.warning("⚠️ No se encontró 'dietas_patologias.json' en la carpeta del proyecto.")
        else:
            dx_con_dieta = [dx for dx in dx_list if dx in dietas_db]
            dx_sin_dieta = [dx for dx in dx_list if dx not in dietas_db]
            if dx_sin_dieta:
                st.warning(f"⚠️ Sin base dietética para: {', '.join(dx_sin_dieta)}")

            if dx_con_dieta:
                st.markdown(f"**Diagnósticos analizados:** {', '.join(dx_con_dieta)}")
                st.markdown("---")

                todos_alimentos = set()
                for dx in dx_con_dieta:
                    datos = dietas_db[dx]
                    todos_alimentos.update(datos.get("permitidos", []))
                    todos_alimentos.update(datos.get("limitados", []))
                    todos_alimentos.update(datos.get("restringidos", []))

                resultado_final = {"permitidos": [], "limitados": [], "restringidos": []}

                for alimento in sorted(todos_alimentos):
                    estados = []
                    for dx in dx_con_dieta:
                        datos = dietas_db[dx]
                        if alimento in datos.get("restringidos", []):   estados.append("restringido")
                        elif alimento in datos.get("limitados", []):    estados.append("limitado")
                        elif alimento in datos.get("permitidos", []):   estados.append("permitido")
                    if not estados: continue
                    if estados.count("restringido") >= 1:
                        resultado_final["restringidos"].append({"Alimento": alimento,
                            "Restringido en": ", ".join([dx for dx in dx_con_dieta if alimento in dietas_db[dx].get("restringidos",[])])})
                    elif estados.count("limitado") >= 1:
                        resultado_final["limitados"].append({"Alimento": alimento,
                            "Limitado en": ", ".join([dx for dx in dx_con_dieta if alimento in dietas_db[dx].get("limitados",[])])})
                    else:
                        resultado_final["permitidos"].append({"Alimento": alimento})

                n_perm  = len(resultado_final["permitidos"])
                n_limit = len(resultado_final["limitados"])
                n_rest  = len(resultado_final["restringidos"])

                c1, c2, c3 = st.columns(3)
                c1.metric("✅ Permitidos",   n_perm,  "Incluir en el plan")
                c2.metric("⚠️ Limitados",   n_limit, "Usar con precaución")
                c3.metric("❌ Restringidos", n_rest,  "Excluir del plan")
                st.markdown("---")

                if resultado_final["permitidos"]:
                    with st.expander(f"✅ ALIMENTOS PERMITIDOS ({n_perm})", expanded=True):
                        st.success("Seguros para TODAS las patologías del paciente.")
                        items = [a["Alimento"] for a in resultado_final["permitidos"]]
                        cols = st.columns(3)
                        for i, item in enumerate(items):
                            cols[i % 3].markdown(f"• {item}")

                if resultado_final["limitados"]:
                    with st.expander(f"⚠️ ALIMENTOS LIMITADOS ({n_limit})", expanded=True):
                        st.warning("Usar en cantidades controladas.")
                        st.dataframe(pd.DataFrame(resultado_final["limitados"]), use_container_width=True, hide_index=True)

                if resultado_final["restringidos"]:
                    with st.expander(f"❌ ALIMENTOS RESTRINGIDOS ({n_rest})", expanded=True):
                        st.error("Excluir del plan dietético.")
                        st.dataframe(pd.DataFrame(resultado_final["restringidos"]), use_container_width=True, hide_index=True)

                st.session_state["dieta_coordinada"] = resultado_final
                st.info(f"💡 Dieta coordinada basada en **{len(dx_con_dieta)} diagnóstico(s)**. Restricción dominante aplicada.")
