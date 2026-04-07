import streamlit as st
import pandas as pd
import os

def render_diagnostico():
    """
    Módulo de diagnóstico nutricional.
    Lee la base de alimentos correctamente desde base.xlsx.
    """
    st.header("📊 Diagnóstico Nutricional")

    archivo = "base.xlsx"

    if not os.path.exists(archivo):
        st.warning(f"⚠️ No se encontró el archivo '{archivo}' en: {os.getcwd()}")
        st.info("Coloque el archivo base.xlsx en la misma carpeta que app.py")
        return

    try:
        df_base = pd.read_excel(archivo)
        df_base.columns = df_base.columns.str.strip()
        st.success(f"✅ Base de alimentos cargada: {len(df_base)} registros.")
        st.dataframe(df_base.head(10), use_container_width=True)
    except Exception as e:
        st.error(f"Error al leer el archivo: {e}")
