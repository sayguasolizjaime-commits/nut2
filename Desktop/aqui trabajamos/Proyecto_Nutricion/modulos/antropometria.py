import streamlit as st
import pandas as pd

def render_antropometria():

    # ================================================================
    # DATOS SIEMPRE EN CERO — Paciente nuevo sin datos anteriores
    # El usuario ingresa todo desde cero cada vez
    # ================================================================
    data = {
        "Determinación": [
            "Peso actual", "Peso habitual", "Talla",
            "Pliegue cutáneo tricipital", "Pliegue cutáneo bicipital",
            "Pliegue cutáneo subescapular", "Pliegue cutáneo suprailiaco",
            "Circunferencia del brazo", "Circunferencia cintura",
            "Circunferencia cadera", "Circunferencia abdominal",
            "Diámetro Ep. Co. Tr.", "Circunferencia muñeca"
        ],
        "Unidad": ["Kg", "kg", "m", "mm", "mm", "mm", "mm", "cm", "cm", "cm", "cm", "cm", "cm"],
        "Dato":   [0.00, 0.00, 0.000, 0.0, 0.0, 0.0, 0.0, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00]
    }

    df = pd.DataFrame(data)

    st.info("💡 Haz doble clic en las celdas de la columna **Dato** para ingresar los valores.")

    # ================================================================
    # TABLA EDITABLE
    # CORRECCIÓN PRINCIPAL: step=0.001 para permitir tallas como
    # 1.68, 1.72, 1.85, etc. sin limitarse a 1.7
    # ================================================================
    df_editado = st.data_editor(
        df,
        use_container_width=True,
        key="editor_antro_resaltado",
        column_config={
            "Dato": st.column_config.NumberColumn(
                "Dato (Ingresar aquí)",
                help="Introduce el valor numérico obtenido en la medición",
                min_value=0.0,
                step=0.001,       # ← CORRECCIÓN: antes era 0.1, ahora acepta 1.68, 1.725, etc.
                format="%.3f",    # ← Muestra 3 decimales para mayor precisión
                required=True,
            ),
            "Determinación": st.column_config.Column(disabled=True),
            "Unidad": st.column_config.Column(disabled=True),
        },
        hide_index=True,
    )

    st.markdown("---")

    # ================================================================
    # INDICADORES DE ALERTA NUTRICIONAL
    # ================================================================
    st.subheader("🚨 Indicadores de Alerta Nutricional")

    try:
        p_act     = float(df_editado.loc[df_editado["Determinación"] == "Peso actual",        "Dato"].values[0])
        p_hab     = float(df_editado.loc[df_editado["Determinación"] == "Peso habitual",      "Dato"].values[0])
        talla_val = float(df_editado.loc[df_editado["Determinación"] == "Talla",              "Dato"].values[0])
        muneca    = float(df_editado.loc[df_editado["Determinación"] == "Circunferencia muñeca", "Dato"].values[0])

        col1, col2, col3 = st.columns(3)

        if talla_val > 0:
            imc_calc = p_act / (talla_val ** 2)
            col1.metric(label="IMC Actual", value=f"{imc_calc:.2f} kg/m²")

            if imc_calc < 16:
                st.error("🔴 Desnutrición severa.")
            elif imc_calc < 17:
                st.error("🔴 Desnutrición moderada.")
            elif imc_calc < 18.5:
                st.warning("🟡 Bajo peso.")
            elif imc_calc < 25:
                st.success("🟢 Estado normal.")
            elif imc_calc < 30:
                st.warning("🟠 Sobrepeso.")
            elif imc_calc < 35:
                st.error("🔴 Obesidad grado I.")
            elif imc_calc < 40:
                st.error("🔴 Obesidad grado II.")
            else:
                st.error("🔴 Obesidad grado III.")

        if p_hab > 0:
            pct_perdida = ((p_hab - p_act) / p_hab) * 100
            es_riesgo = pct_perdida > 5
            col2.metric(
                label="% de Pérdida de Peso",
                value=f"{pct_perdida:.1f}%",
                delta="RIESGO" if es_riesgo else "ESTABLE",
                delta_color="inverse" if es_riesgo else "normal"
            )
            if es_riesgo:
                st.error(f"⚠️ Pérdida significativa ({pct_perdida:.1f}%).")

        with col3:
            st.write("**Ajustes**")
            edema = st.checkbox("¿Presencia de Edema?", key="chk_edema_final_resaltado")
            if edema:
                st.info("ℹ️ Ajuste de peso activo.")

    except Exception:
        st.info("Ingrese datos en la tabla para ver los cálculos.")

    # ================================================================
    # BOTÓN GUARDAR
    # CORRECCIÓN: Guarda el DataFrame completo Y también las variables
    # individuales que necesita valoracion_nutricional.py
    # ================================================================
    if st.button("💾 Guardar Datos Antropométricos", key="btn_save_antro_resaltado"):
        # 1. Guardar DataFrame completo (para calculos.py)
        st.session_state.datos_antropo = df_editado

        # 2. Guardar variables individuales (para valoracion_nutricional.py)
        try:
            st.session_state["a_peso"]   = float(df_editado.loc[df_editado["Determinación"] == "Peso actual",           "Dato"].values[0])
            st.session_state["a_peso_habitual"] = float(df_editado.loc[df_editado["Determinación"] == "Peso habitual",  "Dato"].values[0])
            st.session_state["a_talla"]  = float(df_editado.loc[df_editado["Determinación"] == "Talla",                 "Dato"].values[0])
            st.session_state["a_circunferencia_muneca"] = float(df_editado.loc[df_editado["Determinación"] == "Circunferencia muñeca", "Dato"].values[0])
            st.session_state["a_circ_brazo"]   = float(df_editado.loc[df_editado["Determinación"] == "Circunferencia del brazo",   "Dato"].values[0])
            st.session_state["a_circ_cintura"] = float(df_editado.loc[df_editado["Determinación"] == "Circunferencia cintura",     "Dato"].values[0])
            st.session_state["a_circ_cadera"]  = float(df_editado.loc[df_editado["Determinación"] == "Circunferencia cadera",      "Dato"].values[0])
        except Exception as e:
            st.warning(f"No se pudieron guardar algunas variables: {e}")

        st.success("✅ Datos antropométricos guardados correctamente.")
        st.info(f"Talla registrada: {st.session_state.get('a_talla', 0):.3f} m | Peso: {st.session_state.get('a_peso', 0):.2f} kg")
