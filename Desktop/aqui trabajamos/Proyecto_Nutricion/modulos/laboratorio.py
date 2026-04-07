import streamlit as st
import pandas as pd

def render_laboratorio():
    # 1. DEFINICIÓN DE PARÁMETROS CRÍTICOS (FILOSOFÍA MENOS ES MÁS)
    data = {
        "Parámetro": [
            "Albúmina", "Prealbúmina", "Proteína C Reactiva (PCR)",
            "Linfocitos Totales", "Glucosa", "Creatinina", 
            "Urea", "Hemoglobina"
        ],
        "Unidad": ["g/dL", "mg/dL", "mg/L", "mm³", "mg/dL", "mg/dL", "mg/dL", "g/dL"],
        "Valor": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        "Referencia": ["3.5 - 5.0", "15 - 35", "< 10", "1500 - 4000", "70 - 100", "0.7 - 1.3", "15 - 45", "12 - 16"]
    }
    
    df = pd.DataFrame(data)

    st.info("🧪 Ingrese solo los valores disponibles. La PCR es clave para interpretar la Albúmina.")

    # 2. IMPACTO VISUAL: CONFIGURACIÓN DE LA COLUMNA "VALOR"
    df_editado = st.data_editor(
        df,
        use_container_width=True,
        key="editor_bioquimico_pro",
        column_config={
            "Valor": st.column_config.NumberColumn(
                "Valor (Ingresar aquí)",
                help="Valor reportado por el laboratorio",
                min_value=0.0,
                format="%.2f",
                required=True,
            ),
            "Parámetro": st.column_config.Column(disabled=True),
            "Unidad": st.column_config.Column(disabled=True),
            "Referencia": st.column_config.Column(disabled=True),
        },
        hide_index=True,
    )

    st.markdown("---")

    # 3. INTERPRETACIÓN CLÍNICA AUTOMÁTICA (LO NUEVO)
    st.subheader("📊 Análisis de Inflamación y Proteínas")
    
    try:
        albumina = float(df_editado.loc[df_editado["Parámetro"] == "Albúmina", "Valor"].values[0])
        pcr = float(df_editado.loc[df_editado["Parámetro"] == "Proteína C Reactiva (PCR)", "Valor"].values[0])
        
        c1, c2 = st.columns(2)
        
        # Lógica de interpretación: Albúmina vs Inflamación
        if albumina > 0:
            if albumina < 3.5:
                # Si la albúmina está baja pero la PCR alta, es inflamación, no solo desnutrición
                if pcr > 10:
                    c1.warning(f"Proteína visceral baja ({albumina}) por proceso inflamatorio (PCR: {pcr}).")
                else:
                    c1.error(f"Hipoalbuminemia severa ({albumina}). Posible desnutrición crónica.")
            else:
                c1.success(f"Niveles de albúmina estables ({albumina}).")

        # Registro de Linfocitopenia
        linfos = float(df_editado.loc[df_editado["Parámetro"] == "Linfocitos Totales", "Valor"].values[0])
        if linfos > 0:
            if linfos < 1500:
                c2.error(f"Inmunocompetencia comprometida: {linfos} mm³.")
            else:
                c2.success(f"Conteo de linfocitos normal: {linfos} mm³.")

    except Exception:
        st.caption("Complete Albúmina, PCR y Linfocitos para ver el análisis.")

    # 4. BOTÓN DE GUARDADO
    if st.button("Guardar Bioquímicos", key="btn_save_bio"):
        st.session_state.datos_bioquimicos = df_editado
        st.success("Datos de laboratorio guardados correctamente.")