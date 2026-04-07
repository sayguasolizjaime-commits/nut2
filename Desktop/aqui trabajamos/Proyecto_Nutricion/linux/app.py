import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Sistema Nutricional Hospitalario", layout="wide")
st.title("🏥 Sistema de Gestión Nutricional Hospitalaria")

# --- 0. CARGA DE DATOS ---
def cargar_datos():
    if os.path.exists("listas.xlsx"):
        try:
            xls = pd.ExcelFile("listas.xlsx")
            pats = pd.read_excel(xls, 'Patologias')['Nombre'].dropna().tolist()
            meds = pd.read_excel(xls, 'Medicamentos')['Nombre'].dropna().tolist()
            return pats, meds
        except: return ["Error"], ["Error"]
    return ["Crea listas.xlsx"], ["Crea listas.xlsx"]

lista_patologias, lista_medicamentos = cargar_datos()

# --- DEFINICIÓN DE PESTAÑAS (ESTO DEBE IR ANTES DE USAR TAB3) ---
tab1, tab2, tab3, tab4 = st.tabs(["1. Filiación", "2. Clínica", "3. Anamnesis", "4. Requerimientos"])

# --- CONTENIDO DE PESTAÑAS ---
with tab1:
    st.subheader("1. Datos del Paciente")
    c1, c2, c3 = st.columns(3)
    id_pac = c1.text_input("ID del Paciente")
    nombre = c2.text_input("Nombre Completo")
    tipo_atencion = c3.selectbox("Tipo de Atención", ["Institucional", "Consulta Externa"])
    grupo = st.selectbox("Etapa de la Vida", ["Neonatal", "Adulto", "Adulto Mayor", "Embarazada"])
    st.subheader("2. Datos Antropométricos")
    a1, a2, a3, a4 = st.columns(4)
    sexo = a1.radio("Sexo", ["Masculino", "Femenino"], horizontal=True)
    peso = a2.number_input("Peso (kg)", step=0.1)
    talla = a3.number_input("Talla (cm)", step=1)
    edad = a4.number_input("Edad (años)", step=1)
    imc = peso / ((talla/100) ** 2) if talla > 0 else 0
    a4.metric("IMC", f"{imc:.1f}")

with tab2:
    st.subheader("3. Datos Laboratoriales")
    l1, l2, l3 = st.columns(3)
    alb = l1.number_input("Albúmina (g/dL)", 0.0, 6.0, 3.5)
    creat = l2.number_input("Creatinina (mg/dL)", 0.0, 10.0, 0.9)
    gluc = l3.number_input("Glucosa (mg/dL)", 0, 500, 90)
    st.subheader("4. Datos Médicos")
    pat = st.selectbox("Patología", ["Ninguna"] + lista_patologias)
    m1, m2, m3, m4 = st.columns(4)
    med = m1.selectbox("Medicamento", ["Seleccione..."] + lista_medicamentos)
    dosis = m2.text_input("Dosis/Cantidad")
    hora = m3.time_input("Hora")
    momento = m4.selectbox("Respecto a alimentos", ["Antes", "Junto con", "Después"])

with tab3:
    st.subheader("5. Datos Nutricionales (Anamnesis)")
    if tipo_atencion == "Consulta Externa":
        c5a, c5b = st.columns(2)
        veces_dia = c5a.number_input("Veces al día", 1, 10, 3)
        quien = c5b.text_input("¿Quién prepara?")
        apetito = st.select_slider("¿Cómo es su apetito?", ["Malo", "Regular", "Bueno"])
        pref = st.text_area("Alimentos que prefiere")
    else:
        st.info("Atención Institucional: Anamnesis simplificada.")

with tab4:
    st.subheader("6. Cálculo de Requerimientos")
    r1, r2, r3 = st.columns(3)
    formula = r1.selectbox("Fórmula", ["Mifflin-St Jeor", "Harris-Benedict"])
    act = r2.selectbox("Actividad", ["Sedentario (1.2)", "Ligero (1.375)"])
    f_act = 1.2 if "Sedentario" in act else 1.375
    ajuste = 5 if sexo == "Masculino" else -161
    geb = (10 * peso) + (6.25 * talla) - (5 * edad) + ajuste
    r3.metric("GET Estimado (kcal)", f"{geb * f_act:.0f}")
    st.subheader("7. Prescripción Nutricional")
    indicacion = st.text_area("Indicaciones")