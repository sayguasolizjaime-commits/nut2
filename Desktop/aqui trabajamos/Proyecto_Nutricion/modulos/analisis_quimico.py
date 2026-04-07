import streamlit as st
import pandas as pd
import json
import os

@st.cache_data
def cargar_recursos_analisis():
    # Carga de RDA y Precios respetando tus nombres de archivo
    rda, precios = {}, {}
    if os.path.exists("rda_micronutrientes.json"):
        with open("rda_micronutrientes.json", "r", encoding="utf-8") as f:
            rda = json.load(f)
    if os.path.exists("precios_sucre.json"):
        with open("precios_sucre.json", "r", encoding="utf-8") as f:
            # Tu JSON usa 'precios_por_kg'
            precios = json.load(f).get("precios_por_kg", {})
    return rda, precios

def render_analisis_quimico():
    st.header("🔬 ANÁLISIS QUÍMICO POR TIEMPO DE COMIDA")
    
    # 1. Recuperar datos del paciente para meta RDA
    paciente = st.session_state.get("paciente", {})
    sexo = "M" if paciente.get("sexo") == "Masculino" else "F"
    # Por ahora usamos un rango estándar, luego podemos vincularlo a tu calcular_edad_exacta
    rango_etario = "19-30 años" 
    
    rda_data, precios_kg = cargar_recursos_analisis()
    metas_rda = rda_data.get("rda_por_edad_sexo", {}).get(rango_etario, {}).get(sexo, {})

    # 2. Definición de Columnas (idéntico a tu Word)
    columnas_nutrientes = [
        "Energia", "Prot.", "grasas", "H C", "Fibra", 
        "Ca.", "Fosforo", "Fe.", "Vit. A", "B1", "B2", "Niacina", "Vit C"
    ]
    
    tiempos = ["DESAYUNO", "MEDIA MAÑANA COLACION", "ALMUERZO", "TE", "CENA", "COLACION NOCTURNA"]
    
    # 3. Procesamiento de datos de st.session_state.tablas_dieta
    tablas = st.session_state.get("tablas_dieta", {})
    resumen_filas = []
    total_dia = {col: 0.0 for col in columnas_nutrientes}
    costo_total_bs = 0.0

    for t in tiempos:
        # Buscamos en el diccionario de tablas (normalizamos a minúsculas para coincidir con tu alimentarios.py)
        nombre_key = t.capitalize() if t != "MEDIA MAÑANA COLACION" else "Colación"
        df_t = tablas.get(nombre_key, pd.DataFrame())
        
        fila = {col: 0.0 for col in columnas_nutrientes}
        costo_t = 0.0
        
        if not df_t.empty:
            for col in columnas_nutrientes:
                if col in df_t.columns:
                    val = pd.to_numeric(df_t[col], errors='coerce').sum()
                    fila[col] = round(val, 2)
                    total_dia[col] += val
            
            # Cálculo de costo en Bs (basado en gramos / 1000 * precio_kg)
            if "ALIMENTO" in df_t.columns and "GR" in df_t.columns:
                for _, row in df_t.iterrows():
                    alimento_nom = str(row["ALIMENTO"]).upper()
                    p_kg = precios_kg.get(alimento_nom, 0.0)
                    costo_t += (p_kg * float(row["GR"])) / 1000

        fila["PRECIO/PERSONA"] = f"Bs. {costo_t:.2f}"
        costo_total_bs += costo_t
        resumen_filas.append(fila)

    # 4. Mostrar Tabla Principal
    df_analisis = pd.DataFrame(resumen_filas, index=tiempos)
    st.table(df_analisis)

    # 5. Porcentaje de Adecuación (Comparativa Visual)
    st.markdown("---")
    st.subheader("📊 Porcentaje de Adecuación al 100%")
    
    c1, c2 = st.columns(2)
    with c1:
        st.write("**Macronutrientes**")
        for m in ["Energia", "Prot.", "grasas", "H C"]:
            meta = metas_rda.get(m, 1)
            actual = total_dia[m]
            porc = min(int((actual / meta) * 100), 150) if meta > 0 else 0
            st.caption(f"{m}: {actual:.1f} / {meta} ({porc}%)")
            st.progress(porc / 100 if porc <= 100 else 1.0)

    with c2:
        st.write("**Micronutrientes Críticos**")
        for m in ["Fe.", "Ca.", "Vit C"]:
            meta = metas_rda.get(m, 1)
            actual = total_dia[m]
            porc = min(int((actual / meta) * 100), 150) if meta > 0 else 0
            st.caption(f"{m}: {actual:.1f} / {meta} ({porc}%)")
            st.progress(porc / 100 if porc <= 100 else 1.0)

    st.success(f"💰 Costo Total Estimado: Bs. {costo_total_bs:.2f}")