import streamlit as st
import pandas as pd
import os

# --- CONVERSOR UNIVERSAL ---
CONVERSIONES = {
    "Taza": 200.0, "1/2 Taza": 100.0,
    "Cuchara": 15.0, "Cucharadita": 5.0, "Unidad": 100.0
}

NUTRIENTES = {
    "Energia": "Energía (Kcal)", "Prot.": "Proteínas (g)",
    "grasas": "Grasas (g)", "H C": "H.C. (g)", "Fribra": "Fibra (g)",
    "Ca.": "Calcio (mg)", "Fosforo": "Fósforo (mg)", "Fe.": "Hierro (mg)",
    "Vit. A": "Vit. A (mcg)", "B1": "B1 (mg)", "B2": "B2 (mg)",
    "Niacina": "Niacina (mg)", "Vit C": "Vit. C (mg)"
}

def calcular_nutrientes_fila(df_base, alimento, gramos):
    match = df_base[df_base["ALIMENTO"] == alimento]
    if match.empty or gramos <= 0:
        return {k: 0.0 for k in NUTRIENTES}
    factor = gramos / 100
    return {k: round(float(pd.to_numeric(match[k].values[0], errors="coerce") or 0) * factor, 3)
            for k in NUTRIENTES}

def sumar_nutrientes(lista):
    total = {k: 0.0 for k in NUTRIENTES}
    for d in lista:
        for k in NUTRIENTES:
            total[k] += d.get(k, 0.0)
    return {k: round(v, 2) for k, v in total.items()}

def render_alimentarios_detalle():
    st.header("3. DATOS ALIMENTARIOS")

    # Cargar base
    archivo = "base.xlsx"
    df_base = None
    if os.path.exists(archivo):
        df_base = pd.read_excel(archivo)
        df_base.columns = df_base.columns.str.strip()
        opciones_alimentos = df_base["ALIMENTO"].dropna().unique().tolist()
    else:
        opciones_alimentos = []
        st.warning("⚠️ No se encontró 'base.xlsx'.")

    # Inicializar R24h
    if "r24h_dias" not in st.session_state:
        st.session_state.r24h_dias = {
            "Día 1": pd.DataFrame(columns=["Tiempo","Preparación","Alimento","UMC","Gramos","cc"]),
            "Día 2": pd.DataFrame(columns=["Tiempo","Preparación","Alimento","UMC","Gramos","cc"]),
            "Día 3": pd.DataFrame(columns=["Tiempo","Preparación","Alimento","UMC","Gramos","cc"]),
        }
    if "r24h_tipos" not in st.session_state:
        st.session_state.r24h_tipos = {}

    tab1, tab2, tab3, tab4 = st.tabs([
        "⚡ Hábitos Generales",
        "⚡ Frecuencia de Consumo",
        "⚡ Preferencias",
        "🕒 R24h"
    ])

    # ================================================================
    # PESTAÑA 1: HÁBITOS — todo con clics
    # ================================================================
    with tab1:
        st.subheader("Hábitos Alimentarios")
        st.caption("Seleccione con un clic — sin escribir")

        # Bloque 1: Tiempos de comida y lugar
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.selectbox("Tiempos/día", ["1","2","3","4","5","6"], key="hab_tiempos")
        with c2:
            st.select_slider("Apetito", ["Malo","Regular","Bueno"], key="hab_apetito")
        with c3:
            st.selectbox("Hora de más hambre",
                         ["6:00","7:00","8:00","9:00","10:00","11:00",
                          "12:00","13:00","14:00","15:00","16:00","17:00",
                          "18:00","19:00","20:00","Otro"],
                         key="hab_hora_hambre")
        with c4:
            st.radio("Come entre comidas", ["Sí","No"],
                     horizontal=True, key="hab_entre_comidas")

        # Qué come entre comidas — chips rápidos
        if st.session_state.get("hab_entre_comidas") == "Sí":
            st.multiselect("¿Qué consume entre comidas?",
                           ["Frutas","Galletas","Pan","Yogur","Jugos","Refrescos",
                            "Snacks","Maní","Chocolates","Otro"],
                           key="hab_entre_que")

        st.markdown("---")

        # Bloque 2: Lugar de comidas por días
        st.markdown("**¿Dónde come?**")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.radio("Lunes a Viernes", ["En casa","Fuera de casa","Ambos"],
                     key="hab_lugar_lv", horizontal=True)
        with c2:
            st.radio("Sábado y Domingo", ["En casa","Fuera de casa","Ambos"],
                     key="hab_lugar_fds", horizontal=True)
        with c3:
            quien_opciones = ["Personal del hospital","Familiar","El mismo paciente",
                              "Restaurante","Comedor institucional","Otro"]
            st.selectbox("¿Quién prepara?", quien_opciones, key="hab_quien_prepara")
            st.session_state["lugar_consumo"] = st.session_state.get("hab_quien_prepara","")

        # Horarios rápidos
        st.markdown("**Horarios de comida**")
        horarios_opciones = ["6:00","7:00","8:00","8:30","9:00","10:00","11:00",
                             "12:00","12:30","13:00","14:00","15:00","16:00",
                             "17:00","18:00","19:00","20:00","21:00"]
        c1, c2 = st.columns(2)
        with c1:
            st.multiselect("Horarios L-V:", horarios_opciones, key="hab_horarios_lv")
        with c2:
            st.multiselect("Horarios Sáb-Dom:", horarios_opciones, key="hab_horarios_fds")

        st.markdown("---")

        # Bloque 3: Hidratación
        st.markdown("**Hidratación**")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.select_slider("Vasos agua/día", options=list(range(0,16)),
                             value=8, key="hab_vasos_agua")
        with c2:
            st.select_slider("Vasos otras bebidas/día", options=list(range(0,11)),
                             value=2, key="hab_vasos_otras")
        with c3:
            st.radio("Cambios en fin de semana",
                     ["No","Sí, bebe más","Sí, bebe menos"],
                     key="hab_fds_bebidas")

        st.markdown("---")

        # Bloque 4: Modificaciones recientes
        st.markdown("**Modificaciones recientes**")
        c1, c2 = st.columns(2)
        with c1:
            st.radio("¿Modificó alimentación en 6 meses?",
                     ["No","Sí"], horizontal=True, key="hab_mod_dieta")
        with c2:
            if st.session_state.get("hab_mod_dieta") == "Sí":
                st.multiselect("¿Por qué razón?",
                               ["Enfermedad","Pérdida de peso","Indicación médica",
                                "Económica","Embarazo","Religiosa","Otra"],
                               key="hab_mod_razon")

        # Tiempos habituales — chips
        st.markdown("**Tiempos de comida habituales**")
        st.multiselect("Seleccione todos los que aplican:",
                       ["Desayuno","Media Mañana","Almuerzo","Merienda/Té","Cena","Colación nocturna"],
                       default=["Desayuno","Almuerzo","Cena"],
                       key="hab_tiempos_habitual")

    # ================================================================
    # PESTAÑA 2: FRECUENCIA DE CONSUMO — botones de selección rápida
    # ================================================================
    with tab2:
        st.subheader("Frecuencia de Consumo de Alimentos")
        st.caption("Un clic por fila — sin escribir")

        rubros = [
            "Cereales", "Derivados de Cereales", "Leguminosas",
            "Verduras", "Raíces y Tubérculos", "Frutas",
            "Azúcares y Dulces", "Carnes rojas", "Carnes blancas",
            "Pescados y Mariscos", "Embutidos", "Huevos",
            "Leche y Derivados", "Grasas y Aceites",
            "Bebidas azucaradas", "Misceláneos"
        ]
        frecuencias = ["Diario","Semanal","Quincenal","Mensual","Ocasional","No consume"]

        if "frecuencia_consumo" not in st.session_state:
            st.session_state.frecuencia_consumo = {r: "" for r in rubros}

        # Encabezado
        cols_h = st.columns([2.5,1,1,1,1,1,1])
        cols_h[0].markdown("**Grupo alimentario**")
        for i, f in enumerate(frecuencias):
            cols_h[i+1].markdown(f"**{f}**")

        # Filas con radio buttons horizontales compactos
        for rubro in rubros:
            cols = st.columns([2.5,1,1,1,1,1,1])
            cols[0].markdown(rubro)
            sel = st.session_state.frecuencia_consumo.get(rubro, "")
            for i, frec in enumerate(frecuencias):
                checked = cols[i+1].checkbox(
                    frec, value=(sel == frec),
                    key=f"frec_{rubro}_{frec}",
                    label_visibility="collapsed"
                )
                if checked:
                    st.session_state.frecuencia_consumo[rubro] = frec

    # ================================================================
    # PESTAÑA 3: PREFERENCIAS — todo con selección
    # ================================================================
    with tab3:
        st.subheader("Preferencias y Conductas Alimentarias")
        st.caption("Selección rápida con clics")

        # Alimentos preferidos y no preferidos
        alimentos_comunes = [
            "Naranja","Manzana","Plátano","Papaya","Durazno","Pera","Uva",
            "Pollo","Res","Cerdo","Pescado","Atún","Huevo",
            "Papa","Arroz","Fideo","Pan","Avena","Quinua",
            "Zanahoria","Tomate","Lechuga","Espinaca","Acelga",
            "Leche","Yogur","Queso","Frijoles","Lentejas",
            "Maní","Chocolate","Refresco","Café","Té"
        ]

        c1, c2 = st.columns(2)
        with c1:
            st.multiselect("✅ Alimentos preferidos:",
                           alimentos_comunes, key="pref_preferidos")
        with c2:
            st.multiselect("❌ No le agradan / no acostumbra:",
                           alimentos_comunes, key="pref_no_agrada")

        c1, c2 = st.columns(2)
        with c1:
            st.multiselect("⚠️ Causan malestar:",
                           alimentos_comunes + ["Gluten","Lácteos","Mariscos"],
                           key="pref_malestar")
        with c2:
            alergia = st.radio("¿Alergia alimentaria?",
                               ["No","Sí"], horizontal=True, key="pref_alergia")
            if alergia == "Sí":
                st.multiselect("¿A cuál(es)?",
                               ["Maní","Mariscos","Leche","Huevo","Trigo/Gluten",
                                "Soya","Nueces","Frutas cítricas","Otro"],
                               key="pref_alergia_cual")

        st.markdown("---")

        # Conductas alimentarias — todo con radio/checkbox
        st.markdown("**Conductas**")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.radio("¿Varía consumo con estado emocional?",
                     ["No","Sí — come más","Sí — come menos","Sí — cambia lo que come"],
                     key="pref_varia_emoc")
            st.radio("¿Agrega sal a comida preparada?",
                     ["No","Sí — poco","Sí — moderado","Sí — mucho"],
                     key="pref_sal")
        with c2:
            st.selectbox("Tipo de grasa/aceite:",
                         ["Aceite vegetal","Mantequilla","Margarina",
                          "Grasa animal","Mixto","No usa"],
                         key="pref_grasa_tipo")
            st.selectbox("Cantidad de grasa/aceite:",
                         ["< 5 ml/día","5-10 ml/día","10-20 ml/día","> 20 ml/día"],
                         key="pref_grasa_cant")
        with c3:
            st.radio("¿Dieta especial previa?",
                     ["No","Sí"], horizontal=True, key="pref_dieta_esp")
            st.radio("¿Suplementos/complementos?",
                     ["No","Sí"], horizontal=True, key="pref_suplemento")
            st.radio("¿Medicamentos para bajar peso?",
                     ["No","Sí"], horizontal=True, key="pref_meds_peso")

        # Suplementos — solo si dijo Sí
        if st.session_state.get("pref_suplemento") == "Sí":
            st.multiselect("¿Cuál(es)?",
                           ["Vitamina C","Vitamina D","Complejo B","Hierro","Calcio",
                            "Zinc","Omega 3","Proteína en polvo","Multivitamínico","Otro"],
                           key="pref_suplemento_cual")

        # Dieta especial — solo si dijo Sí
        if st.session_state.get("pref_dieta_esp") == "Sí":
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.selectbox("Tipo de dieta:",
                             ["Hipocalórica","Hiposódica","Diabética","Sin gluten",
                              "Vegetariana","Vegana","Renal","Otra"],
                             key="pref_dieta_tipo")
            with c2:
                st.selectbox("¿Quién indicó?",
                             ["Médico","Nutricionista","Por cuenta propia",
                              "Familiar","Internet","Otro"],
                             key="pref_dieta_quien")
            with c3:
                st.selectbox("¿Hace cuánto?",
                             ["< 1 mes","1-3 meses","3-6 meses",
                              "6-12 meses","> 1 año"],
                             key="pref_dieta_tiempo")
            with c4:
                st.radio("¿Pudo cumplirla?",
                         ["Sí","Parcialmente","No"],
                         key="pref_dieta_cumplio")

    # ================================================================
    # PESTAÑA 4: R24h — con campo Preparación y cc
    # ================================================================
    with tab4:
        st.subheader("Recordatorio de 24 horas")

        col_dia, col_tipo = st.columns([1, 2])
        with col_dia:
            dia_activo = st.selectbox("📅 Día:",
                                      ["Día 1","Día 2","Día 3"],
                                      key="selector_dia_r24")
        with col_tipo:
            tipo_dia = st.radio("Tipo:",
                                ["Día de semana","Fin de semana"],
                                horizontal=True, key=f"tipo_{dia_activo}")
            st.session_state.r24h_tipos[dia_activo] = tipo_dia

        st.markdown("---")

        # Formulario compacto
        c1, c2, c3 = st.columns(3)
        with c1:
            t_comida = st.selectbox("Tiempo",
                                    ["Desayuno","Media Mañana","Almuerzo","Merienda","Cena"],
                                    key="r24_tiempo")
        with c2:
            preparacion = st.text_input("Preparación", key="r24_preparacion",
                                        placeholder="Ej: Sopa de avena")
        with c3:
            sel_alimento = st.selectbox("Ingrediente", opciones_alimentos, key="r24_alimento")

        modo = st.radio("Medida:", ["UMC","Gramos"], horizontal=True, key="r24_modo")
        c_izq, c_der = st.columns(2)
        if modo == "UMC":
            with c_izq:
                umc_sel     = st.selectbox("UMC", list(CONVERSIONES.keys()), key="r24_umc")
                cant_gramos = CONVERSIONES[umc_sel]
                st.info(f"{cant_gramos} gramos")
            with c_der:
                cant_cc = st.number_input("cc", min_value=0.0, step=10.0, key="r24_cc")
        else:
            umc_sel = "N/A"
            with c_izq:
                cant_gramos = st.number_input("Gramos", min_value=0.0, step=1.0, key="r24_gramos")
            with c_der:
                cant_cc = st.number_input("cc", min_value=0.0, step=10.0, key="r24_cc2")

        if st.button("➕ Registrar", key="btn_r24_registrar", type="primary"):
            nueva = {"Tiempo": t_comida, "Preparación": preparacion,
                     "Alimento": sel_alimento, "UMC": umc_sel,
                     "Gramos": cant_gramos, "cc": cant_cc}
            df_actual = st.session_state.r24h_dias[dia_activo]
            for col in ["Tiempo","Preparación","Alimento","UMC","Gramos","cc"]:
                if col not in df_actual.columns:
                    df_actual[col] = ""
            st.session_state.r24h_dias[dia_activo] = pd.concat(
                [df_actual, pd.DataFrame([nueva])], ignore_index=True)
            st.rerun()

        # Tabla del día con análisis químico por tiempo
        df_dia = st.session_state.r24h_dias[dia_activo]
        if not df_dia.empty:
            st.markdown(f"**{dia_activo} — {tipo_dia}**")
            tiempos_orden = ["Desayuno","Media Mañana","Almuerzo","Merienda","Cena"]
            tiempos_en_dia = df_dia["Tiempo"].unique() if "Tiempo" in df_dia.columns else []
            nut_dia_lista = []

            for tiempo in tiempos_orden:
                if tiempo not in tiempos_en_dia:
                    continue
                df_t = df_dia[df_dia["Tiempo"] == tiempo]
                nut_tiempo = []
                with st.expander(f"🍽️ {tiempo}", expanded=False):
                    filas = []
                    for _, row in df_t.iterrows():
                        gramos = float(row.get("Gramos", 0) or 0)
                        n = calcular_nutrientes_fila(df_base, row["Alimento"], gramos) if df_base is not None else {k: 0.0 for k in NUTRIENTES}
                        nut_tiempo.append(n)
                        nut_dia_lista.append(n)
                        fila = {"Preparación": row.get("Preparación",""),
                                "Alimento": row["Alimento"],
                                "UMC": row.get("UMC",""),
                                "Gramos": row.get("Gramos",""),
                                "cc": row.get("cc","")}
                        fila.update({NUTRIENTES[k]: v for k, v in n.items()})
                        filas.append(fila)
                    st.dataframe(pd.DataFrame(filas), use_container_width=True, hide_index=True)
                    sub = sumar_nutrientes(nut_tiempo)
                    st.markdown("**Subtotal:**")
                    st.dataframe(pd.DataFrame([{NUTRIENTES[k]: v for k, v in sub.items()}]),
                                 use_container_width=True, hide_index=True)

            # Total del día
            total_dia = sumar_nutrientes(nut_dia_lista)
            st.session_state[f"r24h_total_{dia_activo}"] = total_dia
            st.markdown("#### 📊 Total del día")
            st.dataframe(pd.DataFrame([{NUTRIENTES[k]: v for k, v in total_dia.items()}]),
                         use_container_width=True, hide_index=True)

            col_del, col_save = st.columns([1, 2])
            with col_del:
                if st.button("🗑️ Eliminar último", key=f"del_{dia_activo}"):
                    st.session_state.r24h_dias[dia_activo] = df_dia.iloc[:-1].reset_index(drop=True)
                    st.rerun()
            with col_save:
                if st.button(f"💾 Guardar {dia_activo}", key=f"save_{dia_activo}", type="primary"):
                    st.session_state[f"r24h_{dia_activo}_guardado"] = True
                    st.success(f"✅ {dia_activo} guardado — {len(df_dia)} registros.")
        else:
            st.info(f"No hay registros para {dia_activo} aún.")

        # Estado de días
        st.markdown("---")
        cols = st.columns(3)
        for i, dia in enumerate(["Día 1","Día 2","Día 3"]):
            df_d     = st.session_state.r24h_dias[dia]
            guardado = st.session_state.get(f"r24h_{dia}_guardado", False)
            tipo_d   = st.session_state.r24h_tipos.get(dia, "—")
            n        = len(df_d) if isinstance(df_d, pd.DataFrame) else 0
            with cols[i]:
                if guardado:
                    st.success(f"✅ {dia} — {n} registros\n{tipo_d}")
                elif n > 0:
                    st.warning(f"⚠️ {dia} — {n} registros\nSin guardar")
                else:
                    st.info(f"⬜ {dia} — Vacío")
