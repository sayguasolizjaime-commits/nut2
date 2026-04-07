import sys
import os

# Agrega la carpeta raíz al PATH
carpeta_raiz = os.path.dirname(os.path.abspath(__file__))
if carpeta_raiz not in sys.path:
    sys.path.insert(0, carpeta_raiz)

import streamlit as st

# =================================================================
# 📜 REGLAS DE ORO DEL PROYECTO (ESTRICTAMENTE OBLIGATORIO)
# =================================================================
# 1. PROTOCOLO QUIRÚRGICO: Solo intervenir el punto solicitado.
# 2. PERSISTENCIA: No borrar st.session_state de tablas existentes.
#    - Medicamentos: st.session_state["ed_meds"] = {"rows": ...}
#    - Fitoterapia: st.session_state["ed_fito_datos"]
# 3. BIBLIOTECA JSON:
#    - Diagnóstico: llaves SIN prefijo "ANT -"
#    - Antecedentes: llaves CON prefijo "ANT -"
# 4. MEMORIA: Antecedentes en st.session_state["m_ant_p_json"]
# 5. ORDEN: @st.cache_data siempre al inicio del módulo.
# 6. FITOTERAPIA: 4 columnas (Planta, Dosis, Forma, Hora).
# 7. IDIOMAS: Prohibido cambiar variables a inglés.
# =================================================================

# --- 1. IMPORTACIÓN DE MÓDULOS ---
try:
    from modulos.filiacion             import render_filiacion
    from modulos.antropometria         import render_antropometria
    from modulos.fisico                import render_examen_fisico
    from modulos.laboratorio           import render_laboratorio
    from modulos.medicos               import render_datos_medicos
    from modulos.psicosocial           import render_psicosocial
    from modulos.alimentarios          import render_datos_alimentarios
    from modulos.alimentarios_detalle  import render_alimentarios_detalle
    from modulos.dieteticos            import render_datos_dieteticos
    from modulos.valoracion_nutricional import render_valoracion_nutricional
    from modulos.actividad             import render_actividad
    from modulos.prescripcion          import render_prescripcion
except ImportError as e:
    st.error(f"⚠️ Error crítico al cargar módulos: {e}")
    st.error(f"📁 Carpeta: {carpeta_raiz}")
    st.error(f"📋 Archivos: {[f for f in os.listdir(os.path.join(carpeta_raiz,'modulos')) if f.endswith('.py')]}")
    st.stop()

# --- 2. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="NutriClinic — Sistema Nutricional Profesional",
    page_icon="🏥",
    layout="wide"
)

# --- 3. NAVEGACIÓN LATERAL ---
with st.sidebar:
    st.title("🏥 MENÚ PRINCIPAL")
    st.markdown("---")
    seccion = st.radio("Navegación:", [
        "📋 RECOLECCIÓN DE DATOS",
        "🔬 VALORACIÓN NUTRICIONAL",
        "🍽️ PRESCRIPCIÓN DIETÉTICA",
        "🧮 HERRAMIENTAS DE CÁLCULO"
    ])
    st.markdown("---")

    # Indicador de paciente activo
    paciente = st.session_state.get("paciente", {})
    nom = paciente.get("nombre", "")
    if nom:
        st.success(f"👤 {nom}")
        edad = paciente.get("edad", "")
        sexo = paciente.get("sexo", "")
        if edad or sexo:
            st.caption(f"{edad} años | {sexo}")
    else:
        st.info("Sin paciente registrado")

    st.markdown("---")
    if st.button("🔄 Nuevo Paciente", type="primary"):
        st.session_state.clear()
        st.rerun()

# --- 4. LÓGICA DE SECCIONES ---
if seccion == "📋 RECOLECCIÓN DE DATOS":
    st.header("📋 RECOLECCIÓN DE DATOS")

    tabs = st.tabs([
        "1. Filiación",
        "2. Médicos",
        "3. Datos Alimentarios",
        "4. Antropometría",
        "5. Bioquímico",
        "6. Psicosocial",
        "7. Actividad Física"
    ])

    with tabs[0]: render_filiacion()
    with tabs[1]: render_datos_medicos()
    with tabs[2]: render_alimentarios_detalle()
    with tabs[3]: render_antropometria()
    with tabs[4]: render_laboratorio()
    with tabs[5]: render_psicosocial()
    with tabs[6]: render_actividad()

elif seccion == "🔬 VALORACIÓN NUTRICIONAL":
    render_valoracion_nutricional()

elif seccion == "🍽️ PRESCRIPCIÓN DIETÉTICA":
    render_prescripcion()

elif seccion == "🧮 HERRAMIENTAS DE CÁLCULO":
    st.header("🧮 HERRAMIENTAS DE CÁLCULO")
    tabs_calc = st.tabs(["Análisis Químico", "Consolidado Dietético"])
    with tabs_calc[0]: render_datos_alimentarios()
    with tabs_calc[1]: render_datos_dieteticos()

# --- 5. PIE DE PÁGINA ---
st.sidebar.markdown("---")
st.sidebar.caption(f"Sección: {seccion.split(' ',1)[1]}")
