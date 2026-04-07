import streamlit as st

def render_psicosocial():
    st.header("👤 Valoración Psicosocial")

    # Inicializar el estado si no existe
    if "perfil_psico" not in st.session_state:
        st.session_state.perfil_psico = {
            "educacion": None,
            "religion": None,
            "sustancias": [],
            "cap_conocimiento": "Medio",
            "cap_aptitud": "Media",
            "cap_practica": "Regular",
            "recursos": "Suficiente"
        }

    # 1. Datos Culturales y Educativos
    st.subheader("Datos Culturales y Educativos")
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.perfil_psico["educacion"] = st.selectbox(
            "Nivel de Educación", 
            ["Sin estudios", "Primaria", "Secundaria", "Técnico Superior", "Universitario", "Posgrado"]
        )
    with col2:
        religiones = ["Católica", "Evangélica/Protestante", "Adventista", "Testigos de Jehová", "Sin religión", "Otras"]
        st.session_state.perfil_psico["religion"] = st.selectbox("Creencias Religiosas", religiones)

    # 2. Consumo de Sustancias
    st.subheader("Hábitos")
    st.session_state.perfil_psico["sustancias"] = st.multiselect(
        "Consumo de sustancias controladas o nocivas:", 
        ["Tabaco", "Alcohol", "Drogas recreativas", "Ninguno"]
    )

    # 3. C.A.P. Alimentario Nutricional
    st.subheader("C.A.P. Alimentario Nutricional")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.session_state.perfil_psico["cap_conocimiento"] = st.select_slider(
            "Conocimiento", ["Bajo", "Medio", "Alto"]
        )
    with c2:
        st.session_state.perfil_psico["cap_aptitud"] = st.select_slider(
            "Aptitud", ["Baja", "Media", "Alta"]
        )
    with c3:
        st.session_state.perfil_psico["cap_practica"] = st.select_slider(
            "Práctica", ["Deficiente", "Regular", "Buena"]
        )

    # 4. Recursos Económicos
    st.subheader("Recursos Económicos")
    st.session_state.perfil_psico["recursos"] = st.select_slider(
        "Capacidad económica para la elaboración de la dieta", 
        ["Muy limitada", "Limitada", "Suficiente", "Holgada"]
    )

    st.text_area("Observaciones psicosociales adicionales", key="obs_psico")