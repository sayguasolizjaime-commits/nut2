import streamlit as st
# CORRECCIÓN: importar desde carpeta raíz, no desde "modulos.calculos"
from calculos import calcular_indicadores

def render_valoracion():
    st.header("VALORACIÓN NUTRICIONAL")

    v1, v2, v3, v4, v5, v6 = st.tabs([
        "Diagnóstico",
        "Fitoterapia",
        "Necesidades Energía",
        "Actividad Física",
        "Análisis 24h",
        "Perfil Nutricional Diario"
    ])

    with v1:
        st.subheader("Diagnóstico Nutricional")
        res = calcular_indicadores()
        if res:
            c1, c2, c3 = st.columns(3)
            c1.metric("IMC Calculado", f"{res['IMC']:.2f} kg/m²")
            c2.metric("Clasificación", res["clasificacion"])
            c3.metric("% Pérdida de Peso", f"{res['pct_perdida']:.1f}%")
        else:
            st.info("Registre los datos antropométricos en la sección de Recolección y presione 'Guardar'.")

    with v2:
        st.subheader("Fitoterapia")
        fito_data = st.session_state.get("ed_fito_datos", [])
        if fito_data:
            st.write(f"Plantas registradas: {len(fito_data)}")
        else:
            st.info("No hay fitoterapia registrada.")

    with v3:
        st.subheader("Necesidades Energéticas")
        st.info("Ver sección completa en Valoración Nutricional → Determinación de Necesidades.")

    with v4:
        st.subheader("Actividad Física")
        tabla = st.session_state.get("tabla_actividades", None)
        if tabla is not None and not tabla.empty:
            st.dataframe(tabla, use_container_width=True)
            total = tabla["Minutos"].sum()
            st.write(f"Total registrado: {total} minutos ({total/60:.1f} horas)")
        else:
            st.info("No hay actividad física registrada.")

    with v5:
        st.subheader("Análisis de 24h")
        df_r24 = st.session_state.get("df_r24", None)
        if df_r24 is not None and not df_r24.empty:
            st.dataframe(df_r24, use_container_width=True)
        else:
            st.info("No hay recordatorio de 24h registrado.")

    with v6:
        st.subheader("Perfil Nutricional Diario")
        st.write("Análisis químico detallado por tiempo de comida.")
        tablas_dieta = st.session_state.get("tablas_dieta", {})
        if any(not df.empty for df in tablas_dieta.values()):
            for tiempo, df in tablas_dieta.items():
                if not df.empty:
                    st.write(f"**{tiempo}**")
                    st.dataframe(df, use_container_width=True)
        else:
            st.info("No hay datos dietéticos registrados aún.")
