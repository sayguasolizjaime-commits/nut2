import streamlit as st
import pandas as pd
import os

def render_datos_alimentarios():
    # 1. RUTA Y CARGA DEL EXCEL
    directorio_script = os.path.dirname(os.path.abspath(__file__))
    archivo = os.path.normpath(os.path.join(directorio_script, "..", "base.xlsx"))

    if not os.path.exists(archivo):
        st.error(f"❌ No se encuentra el archivo en: {archivo}")
        return
    
    try:
        df_base = pd.read_excel(archivo)
        df_base.columns = df_base.columns.str.strip()
    except Exception as e:
        st.error(f"Error al leer el archivo Excel: {e}")
        return

    # Inicializar estado
    if 'tablas_dieta' not in st.session_state:
        st.session_state.tablas_dieta = {t: pd.DataFrame() for t in ["Desayuno", "Almuerzo", "Cena", "Colación"]}

    st.subheader("📋 Panel de Gestión Nutricional")

    # 2. AGREGAR
    with st.expander("➕ Agregar alimento"):
        col1, col2, col3 = st.columns(3)
        t_add = col1.selectbox("Tiempo", ["Desayuno", "Almuerzo", "Cena", "Colación"], key="add_t")
        a_add = col2.selectbox("Alimento", options=df_base["ALIMENTO"].dropna().unique().tolist(), key="add_a")
        g_add = col3.number_input("Gramos", min_value=0.0, step=1.0, key="add_g")
        
        if st.button("Agregar"):
            datos = df_base[df_base["ALIMENTO"] == a_add].iloc[0]
            excluidos = ["ALIMENTO", "Unidad Casera", "Peso Unidad gr", "GR"]
            nueva_fila = {"ALIMENTO": a_add, "GR": g_add}
            
            for col in df_base.columns:
                if col not in excluidos:
                    val = pd.to_numeric(datos[col], errors='coerce') or 0.0
                    nueva_fila[col] = round(val * (g_add / 100), 2)
            
            st.session_state.tablas_dieta[t_add] = pd.concat([st.session_state.tablas_dieta[t_add], pd.DataFrame([nueva_fila])], ignore_index=True)
            st.rerun()

    # 3. MODIFICAR
    with st.expander("✏️ Modificar cantidad"):
        t_mod = st.selectbox("Tiempo", ["Desayuno", "Almuerzo", "Cena", "Colación"], key="mod_t")
        if not st.session_state.tablas_dieta[t_mod].empty:
            a_mod = st.selectbox("Alimento a modificar", st.session_state.tablas_dieta[t_mod]["ALIMENTO"].tolist(), key="mod_a")
            g_mod = st.number_input("Nuevos gramos", min_value=0.0, step=1.0, key="mod_g")
            
            if st.button("Actualizar"):
                idx = st.session_state.tablas_dieta[t_mod].index[st.session_state.tablas_dieta[t_mod]['ALIMENTO'] == a_mod][0]
                base_data = df_base[df_base["ALIMENTO"] == a_mod].iloc[0]
                excluidos = ["ALIMENTO", "Unidad Casera", "Peso Unidad gr", "GR"]
                
                st.session_state.tablas_dieta[t_mod].at[idx, 'GR'] = g_mod
                for col in df_base.columns:
                    if col not in excluidos:
                        val = pd.to_numeric(base_data[col], errors='coerce') or 0.0
                        st.session_state.tablas_dieta[t_mod].at[idx, col] = round(val * (g_mod / 100), 2)
                st.rerun()

    # 4. ELIMINAR
    with st.expander("🗑️ Eliminar alimento"):
        t_del = st.selectbox("Tiempo", ["Desayuno", "Almuerzo", "Cena", "Colación"], key="del_t")
        # Definimos 'a_del' dentro del flujo lógico para evitar el NameError
        if not st.session_state.tablas_dieta[t_del].empty:
            a_del = st.selectbox("Alimento a eliminar", st.session_state.tablas_dieta[t_del]["ALIMENTO"].tolist(), key="del_a")
            if st.button("Eliminar"):
                st.session_state.tablas_dieta[t_del] = st.session_state.tablas_dieta[t_del][st.session_state.tablas_dieta[t_del]['ALIMENTO'] != a_del].reset_index(drop=True)
                st.rerun()
        else:
            st.info("No hay alimentos en este tiempo.")

    # 5. TABLAS DE RESULTADOS
    for tiempo, df in st.session_state.tablas_dieta.items():
        if not df.empty:
            st.write(f"### 🍽️ {tiempo}")
            st.dataframe(df, use_container_width=True)