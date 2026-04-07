import streamlit as st
import pandas as pd
import os

def render_actividad():
    st.header("7. Actividad Física")

    if 'tabla_actividades' not in st.session_state:
        st.session_state.tabla_actividades = pd.DataFrame(columns=["Actividad", "Minutos", "MET"])

    archivo_excel = "compendio_de_actividade_fisicas (1).xlsx"

    if os.path.exists(archivo_excel):
        df_met = pd.read_excel(archivo_excel, skiprows=1)
        df_met.columns = df_met.columns.str.strip()

        c1, c2 = st.columns([2, 1])
        act = c1.selectbox("Actividad:", [""] + df_met["ACTIVIDAD ESPECIFICA"].dropna().unique().tolist(), key="act_main")
        t   = c2.number_input("Tiempo (min):", min_value=0, key="time_main")

        if st.button("➕ Registrar en Tabla", key="btn_reg_act"):
            if act != "" and t > 0:
                mv    = df_met.loc[df_met["ACTIVIDAD ESPECIFICA"] == act, "MET"].values[0]
                nueva = pd.DataFrame({"Actividad": [act], "Minutos": [t], "MET": [mv]})
                st.session_state.tabla_actividades = pd.concat(
                    [st.session_state.tabla_actividades, nueva], ignore_index=True)
                st.rerun()
            else:
                st.warning("Seleccione una actividad e ingrese el tiempo.")
    else:
        st.warning("⚠️ No se encontró el archivo del compendio de actividades físicas.")

    st.markdown("---")

    # Tabla de actividades registradas
    if st.session_state.tabla_actividades.empty:
        st.info("No hay actividades registradas aún. Seleccione una actividad y presione Registrar.")
    else:
        st.table(st.session_state.tabla_actividades)

        total_min = st.session_state.tabla_actividades["Minutos"].sum()
        total_h   = total_min / 60
        st.progress(min(total_min / 1440, 1.0))
        st.write(f"Total: {total_min}/1440 min ({total_h:.1f}h)")

        # Botón eliminar última fila
        col_del, col_save = st.columns([1, 2])
        with col_del:
            if st.button("🗑️ Eliminar última actividad", key="btn_del_act"):
                st.session_state.tabla_actividades = st.session_state.tabla_actividades.iloc[:-1].reset_index(drop=True)
                st.rerun()

        with col_save:
            if st.button("💾 Guardar Registro de Actividad", key="btn_save_act", type="primary"):
                # Los datos ya están en session_state["tabla_actividades"]
                # Este botón confirma que están listos para Valoración
                st.session_state["actividad_guardada"] = True
                st.session_state["actividad_total_min"] = total_min
                st.session_state["actividad_total_h"]   = total_h
                st.success(f"✅ Registro guardado — {len(st.session_state.tabla_actividades)} actividades | {total_h:.1f}h totales")
