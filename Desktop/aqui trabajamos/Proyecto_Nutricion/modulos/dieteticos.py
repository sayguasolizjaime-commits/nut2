import streamlit as st

def render_datos_dieteticos():
    st.header("DATOS DIETÉTICOS ALIMENTARIOS")
    
    # Aquí es donde, en el futuro, integraremos los datos de peso, 
    # talla y los totales de nutrientes del módulo alimentarios.
    
    st.info("Esta sección está lista para recibir el consolidado de datos.")
    
    if "dieta" in st.session_state and not st.session_state.dieta.empty:
        st.write("Se han detectado datos en la sesión. Podemos empezar a procesar la evaluación aquí.")
        # Ejemplo de acceso: st.write(st.session_state.dieta)
    else:
        st.warning("No hay información dietética registrada aún.")