import streamlit as st

def render_examen_fisico():
    st.header("6. Examen Físico Nutricional")
    st.write("Detección cualitativa de pérdida de reservas corporales.")
    
    tab_grasa, tab_musculo, tab_otros = st.tabs(["Reserva Grasa", "Reserva Muscular", "Otros Signos"])
    
    with tab_grasa:
        st.radio("Grasa Subcutánea (Orbital):", ["Normal", "Disminución leve", "Hundimiento severo"])
        st.radio("Reserva en Tríceps:", ["Normal", "Baja", "Muy baja"])
        
    with tab_musculo:
        st.radio("Músculo Temporal (Sienes):", ["Normal", "Plano", "Cóncavo"])
        st.radio("Clavículas/Hombros:", ["Normal", "Prominentes", "Muy prominentes (Hueso visible)"])
        
    with tab_otros:
        piel_pelo = st.multiselect("Hallazgos en Piel/Pelo:", ["Sequedad", "Palidez", "Pelo quebradizo"])
        boca = st.multiselect("Hallazgos en Boca:", ["Glositis", "Estomatitis", "Encías sangrantes"])