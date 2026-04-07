import streamlit as st
import pandas as pd
import json
import os

# ================================================================
# CARGA DE BASES
# ================================================================
@st.cache_data
def cargar_dietas_patologias():
    ruta = "dietas_patologias.json"
    if os.path.exists(ruta):
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return {}
    return {}

@st.cache_data
def cargar_base_alimentos():
    if os.path.exists("base.xlsx"):
        df = pd.read_excel("base.xlsx")
        df.columns = df.columns.str.strip()
        return df
    return pd.DataFrame()

@st.cache_data
def cargar_rda():
    ruta = "rda_micronutrientes.json"
    if os.path.exists(ruta):
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return {}
    return {}

@st.cache_data
def cargar_precios():
    ruta = "precios_sucre.json"
    if os.path.exists(ruta):
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("precios_por_100g", {})
        except: return {}
    return {}


@st.cache_data
def cargar_recetas():
    ruta = "recetas_hospitalarias.json"
    if os.path.exists(ruta):
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return {}
    return {}


@st.cache_data
def cargar_umc():
    ruta = "umc_bolivia.json"
    if os.path.exists(ruta):
        try:
            with open(ruta,"r",encoding="utf-8") as f:
                return json.load(f)
        except: return {}
    return {}

def convertir_a_umc(umc_db, alimento, gramos):
    """Convierte gramos a la UMC más cercana para ese alimento."""
    gramos_a_umc = umc_db.get("gramos_a_umc", {})
    opciones = gramos_a_umc.get(alimento, [])
    if not opciones:
        return f"{gramos:.0f}g"
    # Encontrar la UMC más cercana
    mejor = min(opciones, key=lambda x: abs(x[0] - gramos))
    diferencia_pct = abs(mejor[0] - gramos) / gramos * 100 if gramos > 0 else 100
    # Si la diferencia es menor al 20% usar la UMC, sino mostrar gramos
    if diferencia_pct <= 25:
        return mejor[1]
    else:
        return f"{gramos:.0f}g"

def filtrar_receta(receta, perm_list, rest_list):
    ok, cuidado, excluidos = [], [], []
    for ing in receta.get("ingredientes", []):
        alim = ing["alimento"]
        if rest_list and alim in rest_list:
            excluidos.append(ing)
        elif perm_list and alim not in perm_list:
            cuidado.append(ing)
        else:
            ok.append(ing)
    return ok, cuidado, excluidos

# ================================================================
# NUTRIENTES
# ================================================================
NUTRIENTES = {
    "Energia":"Kcal","Prot.":"Prot(g)","grasas":"Lip(g)",
    "H C":"HC(g)","Fribra":"Fibra(g)","Ca.":"Ca(mg)",
    "Fosforo":"P(mg)","Fe.":"Fe(mg)","Vit. A":"VitA(mcg)",
    "B1":"B1(mg)","B2":"B2(mg)","Niacina":"Niac(mg)","Vit C":"VitC(mg)"
}
NOMBRES = {
    "Energia":"Energía","Prot.":"Proteínas","grasas":"Lípidos",
    "H C":"H.Carbono","Fribra":"Fibra","Ca.":"Calcio",
    "Fosforo":"Fósforo","Fe.":"Hierro","Vit. A":"Vit.A",
    "B1":"B1","B2":"B2","Niacina":"Niacina","Vit C":"Vit.C"
}
UNIDADES = {
    "Energia":"Kcal","Prot.":"g","grasas":"g","H C":"g","Fribra":"g",
    "Ca.":"mg","Fosforo":"mg","Fe.":"mg","Vit. A":"mcg",
    "B1":"mg","B2":"mg","Niacina":"mg","Vit C":"mg"
}

def calc_nut(df_base, alimento, gramos):
    match = df_base[df_base["ALIMENTO"] == alimento]
    if match.empty or gramos <= 0:
        return {k: 0.0 for k in NUTRIENTES}
    factor = gramos / 100
    return {k: round(float(pd.to_numeric(match[k].values[0], errors="coerce") or 0) * factor, 3)
            for k in NUTRIENTES}

def sumar_nut(lista):
    total = {k: 0.0 for k in NUTRIENTES}
    for d in lista:
        for k in NUTRIENTES:
            total[k] += d.get(k, 0.0)
    return {k: round(v, 2) for k, v in total.items()}

def calc_precio(precios_db, alimento, gramos):
    precio_100g = precios_db.get(alimento, 0.0)
    return round(precio_100g * (gramos / 100), 2)

def obtener_grupo_etario(edad, sexo):
    s = "M" if sexo == "Masculino" else "F"
    if edad <= 3:    return "1-3 años", s
    if edad <= 8:    return "4-8 años", s
    if edad <= 13:   return "9-13 años", s
    if edad <= 18:   return "14-18 años", s
    if edad <= 30:   return "19-30 años", s
    if edad <= 50:   return "31-50 años", s
    if edad <= 70:   return "51-70 años", s
    return ">70 años", s

def calcular_rda_ajustada(edad, sexo, dx_list, rda_db):
    grupo, s   = obtener_grupo_etario(edad, sexo)
    rda_grupos = rda_db.get("rda_por_edad_sexo", {})
    ajustes    = rda_db.get("ajustes_por_patologia", {})
    grupo_data = rda_grupos.get(grupo, {})
    rda_base   = grupo_data.get(s, grupo_data.get("M", {})).copy()
    if not rda_base: return {}, {}, grupo
    rda_final  = rda_base.copy()
    notas      = {k: [] for k in NUTRIENTES}
    for dx in dx_list:
        if dx in ajustes:
            for nut, info in ajustes[dx].items():
                if nut in rda_final:
                    rda_final[nut] = round(rda_final[nut] * info.get("factor", 1.0), 2)
                    notas[nut].append(f"[{dx.split(' - ')[0]}] {info['nota']}")
    return rda_final, notas, grupo

def semaforo(pct):
    if pct == 0:           return "⬜"
    elif 90 <= pct <= 110: return "🟢"
    elif 75 <= pct < 90 or 110 < pct <= 125: return "🟡"
    else:                  return "🔴"

# ================================================================
# MÓDULO PRINCIPAL
# ================================================================
def render_prescripcion():
    st.header("🍽️ PRESCRIPCIÓN DIETÉTICA")
    st.markdown("---")

    dietas_db  = cargar_dietas_patologias()
    df_base    = cargar_base_alimentos()
    rda_db     = cargar_rda()
    precios_db = cargar_precios()
    paciente   = st.session_state.get("paciente", {})
    nom        = paciente.get("nombre", st.session_state.get("f_nombre","Paciente"))
    edad       = int(paciente.get("edad", st.session_state.get("f_edad", 30)))
    sexo       = paciente.get("sexo", st.session_state.get("f_sexo","Masculino"))
    peso_act   = st.session_state.get("a_peso", 0.0)
    talla      = st.session_state.get("a_talla", 0.0)
    macro_pta  = st.session_state.get("macro_pta", {})
    macro_ptb  = st.session_state.get("macro_ptb", {})
    dx_list    = st.session_state.get("v_dx_multi", [])
    dx_final   = st.session_state.get("dx_nutricional_final", "")
    eval_antro = st.session_state.get("eval_antro", {})
    imc        = eval_antro.get("imc", 0)

    # Panel resumen
    st.subheader(f"👤 {nom}")
    c1,c2,c3,c4,c5 = st.columns(5)
    c1.metric("Edad", f"{edad} años")
    c2.metric("Sexo", sexo)
    c3.metric("Peso actual", f"{peso_act:.1f} kg")
    c4.metric("Talla", f"{talla:.2f} m")
    c5.metric("IMC", f"{imc:.1f}" if imc else "—")
    if dx_final: st.info(f"**Dx. Nutricional:** {dx_final}")
    if dx_list:  st.caption(f"**Dx. Médicos:** {' | '.join(dx_list)}")
    st.markdown("---")

    # ── PASO 1: REQUERIMIENTO BASE ─────────────────────────────────
    st.subheader("Paso 1 — Requerimiento base")
    kcal_a = macro_pta.get("total_kcal", 0)
    kcal_b = macro_ptb.get("total_kcal", 0)
    if kcal_a == 0 and kcal_b == 0:
        st.warning("⚠️ Complete la Valoración Nutricional primero.")
        return

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**Punto A — Peso Ideal**")
        st.success(f"**{kcal_a:.0f} Kcal** | Prot: {macro_pta.get('gr_prot',0):.1f}g | Lip: {macro_pta.get('gr_lip',0):.1f}g | HC: {macro_pta.get('gr_hc',0):.1f}g")
        st.caption("✅ Prescribir si objetivo es REDUCIR peso (obesidad/sobrepeso) — déficit calórico controlado")
    with col_b:
        st.markdown("**Punto B — Peso Actual**")
        st.info(f"**{kcal_b:.0f} Kcal** | Prot: {macro_ptb.get('gr_prot',0):.1f}g | Lip: {macro_ptb.get('gr_lip',0):.1f}g | HC: {macro_ptb.get('gr_hc',0):.1f}g")
        st.caption("✅ Prescribir si objetivo es MANTENER o RECUPERAR peso (desnutrición/peso normal)")

    base_sel = st.radio("Base para la prescripción:",
        ["Punto A — Peso Ideal","Punto B — Peso Actual"],
        horizontal=True, key="presc_base_sel")

    if base_sel == "Punto A — Peso Ideal":
        req_kcal=kcal_a; req_prot=macro_pta.get("gr_prot",0)
        req_lip=macro_pta.get("gr_lip",0); req_hc=macro_pta.get("gr_hc",0)
    else:
        req_kcal=kcal_b; req_prot=macro_ptb.get("gr_prot",0)
        req_lip=macro_ptb.get("gr_lip",0); req_hc=macro_ptb.get("gr_hc",0)

    st.session_state["presc_req"] = {"kcal":req_kcal,"prot":req_prot,"lip":req_lip,"hc":req_hc}
    st.markdown("---")

    # ── PASO 2: RDA MICRONUTRIENTES AJUSTADA ──────────────────────
    st.subheader("Paso 2 — Requerimientos de micronutrientes")
    rda_final, notas_rda, grupo_etario = calcular_rda_ajustada(edad, sexo, dx_list, rda_db)
    if not rda_final: rda_final = {}
    rda_final["Energia"]=req_kcal; rda_final["Prot."]=req_prot
    rda_final["grasas"]=req_lip;   rda_final["H C"]=req_hc

    st.caption(f"Grupo etario: **{grupo_etario}** | Sexo: **{sexo}**")
    filas_rda = []
    for k, nombre in NOMBRES.items():
        notas_k = notas_rda.get(k, [])
        filas_rda.append({
            "Nutriente": nombre, "Unidad": UNIDADES.get(k,""),
            "RDA": rda_final.get(k,0),
            "Ajuste": "✅ Ajustado" if notas_k else "—",
            "Nota": notas_k[0][:80] if notas_k else "—"
        })
    st.dataframe(pd.DataFrame(filas_rda), use_container_width=True, hide_index=True)
    st.session_state["rda_ajustada"] = rda_final
    st.session_state["notas_rda"]    = notas_rda
    st.markdown("---")

    # ── PASO 3: DISTRIBUCIÓN PORCENTUAL ───────────────────────────
    st.subheader("Paso 3 — Distribución por tiempos de comida")
    todos_tiempos = ["Desayuno","Media Mañana","Almuerzo","Merienda/Té","Cena","Colación nocturna"]
    defaults_pct  = {"Desayuno":20,"Media Mañana":10,"Almuerzo":30,
                     "Merienda/Té":15,"Cena":20,"Colación nocturna":5}
    tiempos_hab   = st.session_state.get("hab_tiempos_habitual",["Desayuno","Almuerzo","Cena"])

    tiempos_activos = st.multiselect(
        "Tiempos de comida:", todos_tiempos,
        default=[t for t in tiempos_hab if t in todos_tiempos] or ["Desayuno","Almuerzo","Cena"],
        key="presc_tiempos_activos")
    if not tiempos_activos:
        st.warning("Seleccione al menos un tiempo.")
        return

    pct_disp  = sum(defaults_pct.get(t,15) for t in tiempos_activos)
    factor_aj = 100/pct_disp if pct_disp>0 else 1

    pcts = {}
    cols_t = st.columns(len(tiempos_activos))
    for i, tiempo in enumerate(tiempos_activos):
        pct_def = round(defaults_pct.get(tiempo,15)*factor_aj)
        with cols_t[i]:
            pcts[tiempo] = st.number_input(tiempo, 0, 100, pct_def, 1, key=f"presc_pct_{tiempo}")

    total_pct = sum(pcts.values())
    if total_pct != 100:
        st.warning(f"⚠️ Suman {total_pct}% — deben ser 100%")
    else:
        st.success("✅ Distribución correcta")

    # Tabla requerimientos por tiempo
    filas_req_t = []
    for tiempo in tiempos_activos:
        pct = pcts[tiempo]/100
        fila = {"Tiempo":tiempo, "%":f"{pcts[tiempo]}%"}
        for k in NUTRIENTES:
            fila[NOMBRES[k]] = round(rda_final.get(k,0)*pct, 2)
        filas_req_t.append(fila)
    st.dataframe(pd.DataFrame(filas_req_t), use_container_width=True, hide_index=True)
    st.session_state["presc_req_tiempos"] = filas_req_t
    st.markdown("---")

    # ── PASO 4: ANÁLISIS QUÍMICO Y COSTO RACIÓN ───────────────────
    st.subheader("Paso 4 — Análisis Químico y Costo Ración")
    st.caption("Estructura hospitalaria: Tiempo → Preparación → Alimentos → Subtotales → Costo/Persona")

    # Cargar biblioteca de recetas
    recetas_db  = cargar_recetas()
    umc_db      = cargar_umc()
    dieta_coord = st.session_state.get("dieta_coordinada", {})
    perm_list   = [a["Alimento"] for a in dieta_coord.get("permitidos",[])]
    rest_list   = [a["Alimento"] for a in dieta_coord.get("restringidos",[])]
    limit_list  = [a["Alimento"] for a in dieta_coord.get("limitados",[])]

    if perm_list:
        opciones_alimentos = perm_list + [f"⚠️ {a}" for a in limit_list]
    elif not df_base.empty:
        opciones_alimentos = df_base["ALIMENTO"].dropna().unique().tolist()
    else:
        opciones_alimentos = []

    # ── SELECTOR DE RECETAS HOSPITALARIAS ─────────────────────
    with st.expander("📚 Biblioteca de Recetas Hospitalarias — Sucre", expanded=False):
        st.caption("Seleccione una receta para cargarla automáticamente con ingredientes filtrados según diagnóstico del paciente")

        categorias_rec = sorted(set(r["categoria"] for r in recetas_db.values()))
        cat_sel = st.selectbox("Categoría:", ["Todas"] + categorias_rec, key="rec_cat")

        if cat_sel == "Todas":
            recetas_filtradas = recetas_db
        else:
            recetas_filtradas = {k:v for k,v in recetas_db.items() if v["categoria"]==cat_sel}

        rec_nombre = st.selectbox("Receta:", list(recetas_filtradas.keys()), key="rec_nombre")

        if rec_nombre and rec_nombre in recetas_filtradas:
            receta_sel = recetas_filtradas[rec_nombre]
            st.markdown(f"**{receta_sel['descripcion']}**")
            st.caption(f"Apta para: {', '.join(receta_sel.get('dieta',[]))}")
            if receta_sel.get("nota"):
                st.info(f"⚕️ {receta_sel['nota']}")

            # Filtrar según diagnóstico
            ing_ok, ing_cuidado, ing_excluidos = filtrar_receta(
                receta_sel, perm_list, rest_list)

            if ing_excluidos:
                st.error(f"❌ Ingredientes EXCLUIDOS por diagnóstico: {', '.join([i['alimento'] for i in ing_excluidos])}")
            if ing_cuidado:
                st.warning(f"⚠️ Usar con precaución: {', '.join([i['alimento'] for i in ing_cuidado])}")

            # Selector de tiempo destino
            tiempo_destino = st.selectbox(
                "Agregar al tiempo:", tiempos_activos, key="rec_tiempo_dest")

            if st.button("⚡ Cargar receta filtrada", key="btn_cargar_receta", type="primary"):
                ingredientes_cargar = ing_ok + ing_cuidado
                if ingredientes_cargar:
                    nuevas_filas = pd.DataFrame([{
                        "Preparación": rec_nombre,
                        "Alimento":    i["alimento"],
                        "Gramos":      i["gramos"]
                    } for i in ingredientes_cargar])
                    if tiempo_destino not in st.session_state.get("presc_plan",{}):
                        st.session_state.setdefault("presc_plan",{})[tiempo_destino] = pd.DataFrame(
                            columns=["Preparación","Alimento","Gramos"])
                    st.session_state.presc_plan[tiempo_destino] = pd.concat(
                        [st.session_state.presc_plan[tiempo_destino], nuevas_filas],
                        ignore_index=True)
                    st.success(f"✅ {len(ingredientes_cargar)} ingredientes cargados en {tiempo_destino}")
                    st.rerun()
                else:
                    st.error("❌ Todos los ingredientes están restringidos para este paciente.")

    st.markdown("---")

    # Inicializar plan
    if "presc_plan" not in st.session_state:
        st.session_state.presc_plan = {}
    for t in todos_tiempos:
        if t not in st.session_state.presc_plan:
            st.session_state.presc_plan[t] = pd.DataFrame(
                columns=["Preparación","Alimento","Gramos"])

    totales_dia = {}

    for tiempo in tiempos_activos:
        pct   = pcts[tiempo]/100
        r_kc  = round(rda_final.get("Energia",0)*pct, 1)
        r_pr  = round(rda_final.get("Prot.",0)*pct, 1)
        r_li  = round(rda_final.get("grasas",0)*pct, 1)
        r_hc  = round(rda_final.get("H C",0)*pct, 1)
        r_fe  = round(rda_final.get("Fe.",0)*pct, 2)
        r_ca  = round(rda_final.get("Ca.",0)*pct, 1)
        r_vc  = round(rda_final.get("Vit C",0)*pct, 1)

        with st.expander(
            f"🍽️ {tiempo} — {pcts[tiempo]}% | "
            f"{r_kc:.0f}Kcal | Prot:{r_pr:.1f}g | "
            f"Fe:{r_fe:.2f}mg | Ca:{r_ca:.0f}mg | VitC:{r_vc:.1f}mg",
            expanded=True
        ):
            # Alertas micronutrientes
            alertas = [notas_rda.get(k,[]) for k in ["Fe.","Ca.","Vit C","B1"]]
            alertas_flat = [n for lista in alertas for n in lista]
            if alertas_flat:
                st.warning(f"⚕️ {alertas_flat[0][:120]}")

            # Formulario con campo PREPARACIÓN
            c1, c2, c3, c4 = st.columns([2, 3, 1, 1])
            with c1:
                preparacion = st.text_input(
                    "Preparación:", key=f"prep_{tiempo}",
                    placeholder="Ej: Sopa de verduras")
            with c2:
                alim_sel = st.selectbox(
                    "Alimento:", opciones_alimentos, key=f"alim_{tiempo}")
            with c3:
                gr_sel = st.number_input(
                    "Gramos:", min_value=0.0, step=5.0, key=f"gr_{tiempo}")
            with c4:
                st.markdown("&nbsp;")
                if st.button("➕", key=f"add_{tiempo}"):
                    alim_limpio = alim_sel.replace("⚠️ ","")
                    nueva = pd.DataFrame([{
                        "Preparación": preparacion,
                        "Alimento":    alim_limpio,
                        "Gramos":      gr_sel
                    }])
                    st.session_state.presc_plan[tiempo] = pd.concat(
                        [st.session_state.presc_plan[tiempo], nueva],
                        ignore_index=True)
                    st.rerun()

            df_t = st.session_state.presc_plan[tiempo]

            if not df_t.empty and not df_base.empty:
                # ── Tabla con nutrientes y precio por alimento ─────
                filas_tabla = []
                for _, row in df_t.iterrows():
                    g    = float(row.get("Gramos",0) or 0)
                    alim = row["Alimento"]
                    n    = calc_nut(df_base, alim, g)
                    prc  = calc_precio(precios_db, alim, g)
                    filas_tabla.append({
                        "Preparación": row.get("Preparación",""),
                        "Alimento":    alim,
                        "GR":          g,
                        "Energía":     n["Energia"],
                        "Prot.":       n["Prot."],
                        "Grasas":      n["grasas"],
                        "H.C.":        n["H C"],
                        "Fibra":       n["Fribra"],
                        "Ca.":         n["Ca."],
                        "Fósforo":     n["Fosforo"],
                        "Fe.":         n["Fe."],
                        "Vit.A":       n["Vit. A"],
                        "B1":          n["B1"],
                        "B2":          n["B2"],
                        "Niacina":     n["Niacina"],
                        "Vit.C":       n["Vit C"],
                        "Bs/Persona":  prc
                    })

                df_tabla = pd.DataFrame(filas_tabla)

                # Subtotales por PREPARACIÓN
                preparaciones = df_tabla["Preparación"].unique()
                for prep in preparaciones:
                    df_prep = df_tabla[df_tabla["Preparación"] == prep]
                    if prep:
                        st.markdown(f"**{prep}**")
                    st.dataframe(df_prep, use_container_width=True, hide_index=True)

                    # Subtotal de la preparación
                    cols_num = ["Energía","Prot.","Grasas","H.C.","Fibra",
                                "Ca.","Fósforo","Fe.","Vit.A","B1","B2",
                                "Niacina","Vit.C","Bs/Persona"]
                    sub_prep = df_prep[cols_num].sum().round(2)
                    df_sub_prep = pd.DataFrame([sub_prep])
                    df_sub_prep.insert(0, "SUBTOTAL", f"Total {prep}" if prep else "Subtotal")
                    st.dataframe(df_sub_prep, use_container_width=True, hide_index=True)
                    st.markdown("---")

                # ── TOTAL DEL TIEMPO (fila resaltada) ─────────────
                cols_num = ["Energía","Prot.","Grasas","H.C.","Fibra",
                            "Ca.","Fósforo","Fe.","Vit.A","B1","B2",
                            "Niacina","Vit.C","Bs/Persona"]
                total_t  = df_tabla[cols_num].sum().round(2)
                costo_t  = total_t["Bs/Persona"]

                st.success(
                    f"**TOTAL {tiempo.upper()}** — "
                    f"Kcal: {total_t['Energía']} | "
                    f"Prot: {total_t['Prot.']}g | "
                    f"Lip: {total_t['Grasas']}g | "
                    f"HC: {total_t['H.C.']}g | "
                    f"Fe: {total_t['Fe.']}mg | "
                    f"Ca: {total_t['Ca.']}mg | "
                    f"VitC: {total_t['Vit.C']}mg | "
                    f"💰 **Bs {costo_t:.2f}/persona**"
                )

                # Semáforo del tiempo
                st.markdown("**Cumplimiento:**")
                c1,c2,c3,c4 = st.columns(4)
                def barra(label, cons, req):
                    p = round((cons/req)*100,1) if req>0 else 0
                    return f"{semaforo(p)} {label}: {cons:.1f}/{req:.1f} ({p}%)"
                c1.markdown(barra("Kcal", total_t["Energía"], r_kc))
                c2.markdown(barra("Prot", total_t["Prot."],   r_pr))
                c3.markdown(barra("Fe",   total_t["Fe."],     r_fe))
                c4.markdown(barra("VitC", total_t["Vit.C"],   r_vc))

                # Guardar nutrientes del tiempo
                totales_dia[tiempo] = {
                    "Energia": total_t["Energía"], "Prot.":   total_t["Prot."],
                    "grasas":  total_t["Grasas"],  "H C":     total_t["H.C."],
                    "Fribra":  total_t["Fibra"],   "Ca.":     total_t["Ca."],
                    "Fosforo": total_t["Fósforo"], "Fe.":     total_t["Fe."],
                    "Vit. A":  total_t["Vit.A"],   "B1":      total_t["B1"],
                    "B2":      total_t["B2"],       "Niacina": total_t["Niacina"],
                    "Vit C":   total_t["Vit.C"],   "costo":   costo_t
                }

                # ── COMPLEMENTO INTELIGENTE ────────────────────
                st.markdown("---")
                st.markdown("**💡 Complemento para llegar al 90-100%**")

                pct_kcal_actual = round((total_t["Energía"]/r_kc)*100,1) if r_kc>0 else 0

                col_aj1, col_aj2 = st.columns([2,1])
                with col_aj1:
                    objetivo_pct = st.slider(
                        "Objetivo de adecuación calórica:",
                        min_value=80, max_value=110, value=95, step=1,
                        key=f"slider_obj_{tiempo}"
                    )
                with col_aj2:
                    ico = semaforo(pct_kcal_actual)
                    st.metric("Adecuación actual", f"{pct_kcal_actual}%",
                              delta=f"{objetivo_pct-pct_kcal_actual:+.1f}% necesario")

                kcal_faltante = (r_kc * objetivo_pct/100) - total_t["Energía"]

                if pct_kcal_actual >= objetivo_pct:
                    st.success(f"✅ Ya cubre el {pct_kcal_actual}% — dentro del objetivo {objetivo_pct}%")
                elif total_t["Energía"] == 0:
                    st.warning("Agregue alimentos primero.")
                else:
                    st.warning(f"⚠️ Faltan **{kcal_faltante:.0f} Kcal** para llegar al {objetivo_pct}%")

                    # Calcular déficit de micronutrientes
                    micro_mapa = {
                        "Fe.":    ("Hierro",     r_fe,
                                   [("HIGADO",5),("CARNE DE RES",10),("LENTEJA",8),
                                    ("ESPINACA",3),("QUINUA",5)]),
                        "Ca.":    ("Calcio",     r_ca,
                                   [("LECHE ENTERA",6),("YOGUR NATURAL",5),
                                    ("QUESO FRESCO",3),("ESPINACA",3)]),
                        "Vit C":  ("Vitamina C", r_vc,
                                   [("NARANJA",5),("LIMON",3),("TOMATE",5),("BROCOLI",5)]),
                        "Vit. A": ("Vitamina A", rda_final.get("Vit. A",0)*pct,
                                   [("ZANAHORIA",5),("ESPINACA",3),("ZAPALLO",5)]),
                        "B1":     ("B1 Tiamina", rda_final.get("B1",0)*pct,
                                   [("AVENA",5),("QUINUA",5),("LENTEJA",8)]),
                    }

                    # Encontrar mejores alimentos complementarios
                    if not df_base.empty:
                        sugerencias = []
                        for alim_s in opciones_alimentos[:50]:
                            alim_s_limpio = alim_s.replace("⚠️ ","")
                            # Calcular con 30g como porción de complemento
                            n_s = calc_nut(df_base, alim_s_limpio, 30)
                            kcal_s = n_s.get("Energia",0)
                            if kcal_s <= 0: continue

                            # Porciones reales: cuántas porciones de 30g cubro el déficit
                            porciones = max(1, round(kcal_faltante / kcal_s))
                            porciones = min(porciones, 3)  # máximo 3 porciones
                            gr_sug    = 30 * porciones
                            n_final   = calc_nut(df_base, alim_s_limpio, gr_sug)
                            kcal_final = n_final.get("Energia",0)

                            # Verificar qué micronutrientes cubre
                            mapa_cols = {"Fe.":"Fe.","Ca.":"Ca.","Vit C":"Vit.C","Vit. A":"Vit.A","B1":"B1"}
                            micros_cubiertos = []
                            for k_m, (nom_m, req_m, _) in micro_mapa.items():
                                if req_m > 0:
                                    col_t  = mapa_cols.get(k_m, k_m)
                                    cons_m = total_t.get(col_t, 0)
                                    pct_m  = round((cons_m/req_m)*100,1)
                                    if pct_m < 75 and n_final.get(k_m,0) > 0:
                                        micros_cubiertos.append(nom_m)

                            umc_s = convertir_a_umc(umc_db, alim_s_limpio, gr_sug)
                            sugerencias.append({
                                "alimento":   alim_s_limpio,
                                "umc":        umc_s,
                                "gramos":     gr_sug,
                                "kcal":       round(kcal_final,1),
                                "pct_cubre":  round((kcal_final/kcal_faltante)*100,1),
                                "micros":     micros_cubiertos,
                                "score":      kcal_final + len(micros_cubiertos)*50
                            })

                        # Ordenar por score y mostrar top 5
                        sugerencias = sorted(sugerencias, key=lambda x: x["score"], reverse=True)[:5]

                        if sugerencias:
                            st.markdown("**Alimentos que puedes agregar para completar el requerimiento:**")
                            for sug in sugerencias:
                                micros_str = f" | También aporta: {', '.join(sug['micros'])}" if sug['micros'] else ""
                                col_s1, col_s2 = st.columns([3,1])
                                with col_s1:
                                    st.info(
                                        f"➕ **{sug['alimento'].title()}** — "
                                        f"{sug['umc']} ({sug['gramos']}g) → "
                                        f"+{sug['kcal']} Kcal ({sug['pct_cubre']}% del déficit)"
                                        f"{micros_str}"
                                    )
                                with col_s2:
                                    if st.button(f"➕ Agregar", key=f"sug_add_{tiempo}_{sug['alimento']}"):
                                        prep_actual = st.session_state.get(f"prep_{tiempo}","Complemento")
                                        nueva_fila  = pd.DataFrame([{
                                            "Preparación": prep_actual or "Complemento",
                                            "Alimento":    sug["alimento"],
                                            "Gramos":      sug["gramos"]
                                        }])
                                        st.session_state.presc_plan[tiempo] = pd.concat(
                                            [st.session_state.presc_plan[tiempo], nueva_fila],
                                            ignore_index=True)
                                        st.rerun()

                # Déficit de micronutrientes independiente de Kcal
                st.markdown("**Estado de micronutrientes:**")
                micro_mapa2 = {
                    "Fe.":    ("Hierro",     r_fe),
                    "Ca.":    ("Calcio",     r_ca),
                    "Vit C":  ("Vitamina C", r_vc),
                    "Vit. A": ("Vitamina A", rda_final.get("Vit. A",0)*pct),
                    "B1":     ("B1",         rda_final.get("B1",0)*pct),
                }
                mapa_cols2 = {"Fe.":"Fe.","Ca.":"Ca.","Vit C":"Vit.C","Vit. A":"Vit.A","B1":"B1"}
                cols_micro = st.columns(5)
                for i, (k_m, (nom_m, req_m)) in enumerate(micro_mapa2.items()):
                    col_t2 = mapa_cols2.get(k_m, k_m)
                    cons_m = total_t.get(col_t2, 0)
                    pct_m = round((cons_m/req_m)*100,1) if req_m>0 else 0
                    cols_micro[i].metric(
                        nom_m,
                        f"{cons_m:.1f}",
                        f"{semaforo(pct_m)} {pct_m}%"
                    )

                st.markdown("---")
                # Eliminar último
                if st.button("🗑️ Eliminar último", key=f"del_{tiempo}"):
                    st.session_state.presc_plan[tiempo] = df_t.iloc[:-1].reset_index(drop=True)
                    st.rerun()

            else:
                st.info("Agregue alimentos a este tiempo.")
                totales_dia[tiempo] = {k: 0.0 for k in NUTRIENTES}

    st.markdown("---")

    # ── PASO 5: RESUMEN TOTAL + RECETA EN UMC ─────────────────────
    st.subheader("Paso 5 — Análisis Químico Total y Receta Dietética")

    if totales_dia:
        total_g   = sumar_nut([{k:v for k,v in d.items() if k in NUTRIENTES}
                                for d in totales_dia.values()])
        costo_dia = sum(d.get("costo",0) for d in totales_dia.values())

        # Tabla comparativa
        filas_comp = []
        for k, nombre in NOMBRES.items():
            consumido = total_g.get(k,0)
            requerido = rda_final.get(k,0)
            pct_ad    = round((consumido/requerido)*100,1) if requerido>0 else 0
            notas_k   = notas_rda.get(k,[])
            filas_comp.append({
                "Nutriente":    nombre,
                "Unidad":       UNIDADES.get(k,""),
                "Consumido":    consumido,
                "Requerido":    requerido,
                "% Adec.":      f"{pct_ad}%",
                "Estado":       semaforo(pct_ad),
                "Nota clínica": notas_k[0][:70] if notas_k else "—"
            })
        st.dataframe(pd.DataFrame(filas_comp), use_container_width=True, hide_index=True)

        # Costos
        st.markdown("---")
        c1,c2,c3 = st.columns(3)
        c1.metric("💰 Costo/día",     f"Bs {costo_dia:.2f}")
        c2.metric("💰 Costo promedio/tiempo", f"Bs {costo_dia/len(totales_dia):.2f}")
        c3.metric("📅 Costo mensual", f"Bs {costo_dia*30:.2f}")

        # Alertas
        criticos = [f for f in filas_comp if f["Estado"]=="🔴"]
        if criticos:
            st.markdown("#### 🚨 Nutrientes que requieren ajuste:")
            for c_item in criticos:
                st.error(f"**{c_item['Nutriente']}** — {c_item['% Adec.']} | {c_item['Nota clínica']}")
        else:
            st.success("✅ Plan adecuado en todos los nutrientes.")

        st.session_state["plan_nutricional_final"] = {
            "total": total_g, "rda": rda_final,
            "costo_dia": costo_dia, "evaluacion": filas_comp
        }

        st.markdown("---")

        # ── RECETA DIETÉTICA EN TABLA UMC ─────────────────────
        st.subheader("📋 Receta Dietética")
        st.caption("Plan de alimentación en Unidades de Medida Casera")

        for tiempo_r in tiempos_activos:
            df_r = st.session_state.presc_plan.get(tiempo_r, pd.DataFrame())
            if df_r.empty: continue

            st.markdown(f"**🍽️ {tiempo_r}**")
            filas_receta = []
            preparaciones_r = df_r["Preparación"].unique() if "Preparación" in df_r.columns else [""]

            for prep_r in preparaciones_r:
                df_p = df_r[df_r["Preparación"]==prep_r] if "Preparación" in df_r.columns else df_r
                for _, row_r in df_p.iterrows():
                    alim_r = row_r["Alimento"]
                    gr_r   = float(row_r.get("Gramos",0) or 0)
                    umc_r  = convertir_a_umc(umc_db, alim_r, gr_r)
                    # Calcular nutrientes reales de esa porción UMC
                    n_r    = calc_nut(df_base, alim_r, gr_r) if not df_base.empty else {}
                    filas_receta.append({
                        "Preparación": prep_r if prep_r else "—",
                        "Alimento":    alim_r.title(),
                        "UMC":         umc_r,
                        "Gramos":      f"{gr_r:.0f}g",
                        "Kcal":        n_r.get("Energia",0),
                        "Prot(g)":     n_r.get("Prot.",0),
                        "Lip(g)":      n_r.get("grasas",0),
                        "HC(g)":       n_r.get("H C",0),
                        "Fe(mg)":      n_r.get("Fe.",0),
                        "Ca(mg)":      n_r.get("Ca.",0),
                        "VitC(mg)":    n_r.get("Vit C",0),
                    })

            if filas_receta:
                df_rec = pd.DataFrame(filas_receta)
                st.dataframe(df_rec, use_container_width=True, hide_index=True)

                # Fila total del tiempo en UMC
                tot_r = {
                    "Preparación":"TOTAL","Alimento":"","UMC":"","Gramos":"",
                    "Kcal":       round(sum(f["Kcal"]    for f in filas_receta),1),
                    "Prot(g)":    round(sum(f["Prot(g)"] for f in filas_receta),1),
                    "Lip(g)":     round(sum(f["Lip(g)"]  for f in filas_receta),1),
                    "HC(g)":      round(sum(f["HC(g)"]   for f in filas_receta),1),
                    "Fe(mg)":     round(sum(f["Fe(mg)"]  for f in filas_receta),2),
                    "Ca(mg)":     round(sum(f["Ca(mg)"]  for f in filas_receta),1),
                    "VitC(mg)":   round(sum(f["VitC(mg)"]for f in filas_receta),1),
                }
                st.dataframe(pd.DataFrame([tot_r]), use_container_width=True, hide_index=True)
            st.markdown("---")

        if st.button("💾 Guardar Plan Completo", type="primary", key="btn_save_plan"):
            st.success("✅ Plan nutricional guardado correctamente.")
            st.balloons()
