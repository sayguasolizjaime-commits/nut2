import streamlit as st
import pandas as pd
import json
import os

# --- 1. FUNCIONES DE CARGA ---

@st.cache_data
def cargar_biblioteca_json():
    """Carga el diccionario principal de patologías y antecedentes."""
    ruta = "biblioteca.json"
    if os.path.exists(ruta):
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

@st.cache_data
def cargar_vademecum_json():
    """Carga la lista de medicamentos químicos."""
    ruta = "medicamentos.json"
    if os.path.exists(ruta):
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("vademecum", [])
        except Exception:
            return []
    return []

@st.cache_data
def cargar_vademecum_fito_json():
    """Carga la lista de plantas medicinales."""
    ruta = "fitoterapia.json"
    if os.path.exists(ruta):
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("plantas", [])
        except Exception:
            return []
    return []

# --- 2. FUNCIÓN PRINCIPAL DEL MÓDULO ---

def render_datos_medicos():
    # Carga de datos inicial
    biblioteca = cargar_biblioteca_json()
    
    # FILTRADO: Separamos Diagnósticos de Antecedentes
    lista_pat_json = sorted([k for k in biblioteca.keys() if not k.startswith("ANT -")])
    lista_ant_json = sorted([k for k in biblioteca.keys() if k.startswith("ANT -")])
    
    vademecum = cargar_vademecum_json()
    vademecum_fito = cargar_vademecum_fito_json()
    opciones_meds = [f"{m['quimico']} ({', '.join(m['comercial'])})" for m in vademecum]

    # --- SECCIÓN I: DIAGNÓSTICO MÉDICO ACTUAL ---
    st.subheader("🏥 Diagnóstico Médico Actual")
    st.session_state["v_dx_multi"] = st.multiselect(
        "Seleccione patologías diagnosticadas (Motivo de consulta):", 
        options=lista_pat_json, 
        default=st.session_state.get("v_dx_multi", []),
        key="temp_dx"
    )

    st.markdown("---")

    # --- SECCIÓN II: ANTECEDENTES PERSONALES ---
    st.subheader("🏃 Antecedentes Personales")
    st.session_state["m_ant_p_json"] = st.multiselect(
        "Antecedentes con Impacto Nutricional (desde Biblioteca):", 
        options=lista_ant_json, 
        default=st.session_state.get("m_ant_p_json", []), 
        key="key_ant_json_persist"
    )

    st.session_state["m_ant_p_libre"] = st.text_area(
        "Otros antecedentes o detalles quirúrgicos específicos:",
        value=st.session_state.get("m_ant_p_libre", ""),
        key="key_ant_libre_persist"
    )

    st.markdown("---")

    # --- SECCIÓN III: ANTECEDENTES FAMILIARES (RESTAURADO) ---
    st.subheader("👨‍👩‍👧‍👦 Registro de Antecedentes Familiares")
    
    # Inicialización de las listas de persistencia
    if "lista_observaciones_ant" not in st.session_state:
        st.session_state["lista_observaciones_ant"] = []
    if "m_ant_f_json" not in st.session_state:
        st.session_state["m_ant_f_json"] = []

    col_fam, col_est, col_pat = st.columns([1, 1, 2])
    with col_fam: 
        fam = st.selectbox("Familiar:", ["Madre", "Padre", "Abuelo/a Pat.", "Abuelo/a Mat.", "Hermano/a", "Tío/a"], key="f_fam")
    with col_est: 
        est = st.selectbox("Estado:", ["falleció con", "vive con", "tiene antecedente de"], key="f_est")
    with col_pat: 
        pat = st.selectbox("Patología:", lista_pat_json, key="f_pat")

    if st.button("➕ Añadir a cuadro", use_container_width=True):
        # 1. Guardar frase descriptiva (Para visualización)
        nueva_frase = f"{fam} {est} {pat}"
        
        if nueva_frase not in st.session_state["lista_observaciones_ant"]:
            st.session_state["lista_observaciones_ant"].append(nueva_frase)
            
            # 2. REGLA DE ORO: Guardar objeto completo para Valoración
            # Guardamos un diccionario con el 'rol' y la 'patologia'
            registro_familiar = {
                "descripcion_visual": nueva_frase,
                "patologia_clave": pat
            }
            st.session_state["m_ant_f_json"].append(registro_familiar)
            st.rerun()

    # Resumen visual
    resumen_fam = "\n".join([f"- {item}" for item in st.session_state["lista_observaciones_ant"]])
    st.session_state["m_ant_f_orig"] = st.text_area(
        "Resumen de Antecedentes Familiares (Visual):", 
        value=resumen_fam, 
        height=120
    )
    
    if st.button("🗑️ Limpiar historial familiar"):
        st.session_state["lista_observaciones_ant"] = []
        st.session_state["m_ant_f_json"] = [] # Se limpian ambos para resetear Valoración
        st.rerun()

    # --- SECCIÓN IV: MEDICAMENTOS ---
    st.markdown("---")
    st.markdown("### 💊 Medicamentos")
    if "df_meds_persistencia" not in st.session_state:
        st.session_state.df_meds_persistencia = pd.DataFrame(columns=["Medicamento", "Dosis", "Frecuencia"])
    
    df_meds_edit = st.data_editor(
        st.session_state.df_meds_persistencia, 
        num_rows="dynamic", 
        use_container_width=True, 
        key="editor_meds_vfinal",
        column_config={
            "Medicamento": st.column_config.SelectboxColumn("Medicamento", options=opciones_meds, width="large")
        }
    )

    if st.button("💾 GUARDAR MEDICAMENTOS", type="primary", use_container_width=True):
        # 1. Capturamos los cambios crudos del editor (esto es lo que causaba el error)
        cambios_m = st.session_state.get("editor_meds_vfinal", {})
        
        # 2. Partimos de la base de datos que ya teníamos guardada
        df_base_meds = st.session_state.df_meds_persistencia.copy()

        # 3. PROCESAR EDICIONES (El diccionario que daba error)
        edited_rows = cambios_m.get("edited_rows", {})
        for idx, cambios_fila in edited_rows.items():
            for col, val in cambios_fila.items():
                df_base_meds.at[idx, col] = val

        # 4. PROCESAR FILAS NUEVAS (La lista de nuevas entradas)
        added_rows = cambios_m.get("added_rows", [])
        if added_rows:
            df_nuevos_m = pd.DataFrame(added_rows)
            df_base_meds = pd.concat([df_base_meds, df_nuevos_m], ignore_index=True)

        # 5. PROCESAR ELIMINACIONES
        deleted_rows = cambios_m.get("deleted_rows", [])
        if deleted_rows:
            df_base_meds = df_base_meds.drop(deleted_rows).reset_index(drop=True)

        # 6. LIMPIEZA FINAL Y GUARDADO
        # Solo guardamos si se seleccionó un nombre de medicamento
        df_final_meds = df_base_meds.dropna(subset=["Medicamento"]).copy()
        
        # Guardamos para la tabla visual (persistencia)
        st.session_state.df_meds_persistencia = df_final_meds
        
        # Guardamos para el módulo de Valoración (formato compatible)
        st.session_state["ed_meds"] = {"rows": df_final_meds.to_dict('records')}
        
        st.success(f"✅ Se han procesado {len(df_final_meds)} medicamentos correctamente.")
        
        # Forzamos refresco para que el editor se limpie y muestre la realidad
        st.rerun()

    # --- SECCIÓN V: FITOTERAPIA ---
    st.markdown("---")
    st.markdown("### 🌿 Registro de Fitoterapia")

    opciones_formas = ["Infusión", "Decocción", "Macerado", "Cápsula", "Extracto Fluido", "Tintura Madre"]
    opciones_dosis_f = ["1 Taza", "1/2 Taza", "1 Vaso", "15 ml", "30 ml", "1 Cucharada", "1 Cápsula"]
    opciones_horas_fito = ["06:00 AM (Ayunas)", "08:00 AM (Desayuno)", "10:00 AM (Media Mañana)", "12:00 PM (Almuerzo)", "04:00 PM (Media Tarde)", "07:00 PM (Cena)", "10:00 PM (Antes de dormir)"]

    if "df_fito_persistencia" not in st.session_state:
        st.session_state.df_fito_persistencia = pd.DataFrame(columns=["Planta", "Dosis", "Forma", "Hora"])

    # Eliminamos el uso de 'df_fito_editado' directo en el botón y usamos la key del editor
    st.data_editor(
        st.session_state.df_fito_persistencia,
        num_rows="dynamic",
        use_container_width=True,
        key="editor_fito_final_v2", # Esta key es vital
        column_config={
            "Planta": st.column_config.SelectboxColumn("🌿 Planta", options=sorted([p["nombre"] for p in vademecum_fito]), required=True),
            "Dosis": st.column_config.SelectboxColumn("⚖️ Dosis", options=opciones_dosis_f),
            "Forma": st.column_config.SelectboxColumn("⚗️ Forma", options=opciones_formas),
            "Hora": st.column_config.SelectboxColumn("⏰ Hora", options=opciones_horas_fito, required=True)
        },
        hide_index=True,
    )

    if st.button("💾 GUARDAR FITOTERAPIA", use_container_width=True, type="primary"):
        # 1. Obtenemos los cambios del estado del editor
        cambios = st.session_state["editor_fito_final_v2"]
        
        # 2. Recuperamos el DataFrame original de la sesión
        df_fito = st.session_state.df_fito_persistencia.copy()
        
        # 3. Aplicar FILAS EDITADAS (Es un dict: {indice: {columna: valor}})
        for indice, cambios_fila in cambios.get("edited_rows", {}).items():
            for columna, nuevo_valor in cambios_fila.items():
                df_fito.at[indice, columna] = nuevo_valor
        
        # 4. Aplicar FILAS AGREGADAS (Es una lista de dicts)
        filas_nuevas = cambios.get("added_rows", [])
        if filas_nuevas:
            df_nuevas = pd.DataFrame(filas_nuevas)
            df_fito = pd.concat([df_fito, df_nuevas], ignore_index=True)
            
        # 5. Aplicar FILAS ELIMINADAS (Es una lista de índices)
        indices_borrados = cambios.get("deleted_rows", [])
        if indices_borrados:
            df_fito = df_fito.drop(indices_borrados).reset_index(drop=True)

        # 6. LIMPIEZA Y PERSISTENCIA FINAL
        # Solo guardamos si la planta tiene nombre (evitar filas vacías)
        df_final = df_fito[df_fito["Planta"].notna()].copy()
        
        # Actualizamos estados de sesión
        st.session_state["ed_fito_datos"] = df_final.to_dict('records')
        st.session_state.df_fito_persistencia = df_final
        
        st.success(f"✅ Se procesaron {len(df_final)} registros de fitoterapia correctamente.")
        st.rerun()

# --- SECCIÓN: Necesidades de energia ---
    st.markdown("---")
    st.subheader("Necesidades de energia")
    
    # Espacio reservado para desarrollo futuro