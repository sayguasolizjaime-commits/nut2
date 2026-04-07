import streamlit as st
from utilidades import cargar_lista, calcular_edad_exacta
from datetime import date

def render_filiacion():
    # Inicialización del estado
    if "paciente" not in st.session_state:
        st.session_state.paciente = {
            "nombre": "", "id_seguro": "", "sexo": "Femenino", "edad": 0,
            "f_nac": None, "nacionalidad": "Boliviana", "telefono": "",
            "direccion": "", "ocupacion": "Estudiante", "estado_civil": "Soltero(a)"
        }

    st.header("1. DATOS DEL PACIENTE (FILIACIÓN)")

    provincias_por_dpto = {
        "Chuquisaca": ["Oropeza", "Juana Azurduy de Padilla", "Belisario Boeto", "Tomina", "Hernando Siles", "Yamparáez", "Nor Cinti", "Sud Cinti", "Jaime Zudáñez"],
        "La Paz":     ["Murillo", "Ingavi", "Los Andes", "Omasuyos", "Pacajes", "Camacho", "Muñecas", "Larecaja", "Loayza", "Inquisivi"],
        "Cochabamba": ["Cercado", "Campero", "Ayopaya", "Esteban Arce", "Arani", "Arque", "Capinota", "Germán Jordán", "Quillacollo", "Chapare"],
        "Oruro":      ["Cercado", "Abaroa", "Carangas", "Sajama", "Litoral", "Poopó", "Pantaleón Dalence", "Sud Carangas", "Ladislao Cabrera"],
        "Potosí":     ["Tomás Frías", "Rafael Bustillo", "Cornelio Saavedra", "Chayanta", "Charcas", "Nor Chichas", "Sud Chichas", "Daniel Campos", "Nor Lípez"],
        "Tarija":     ["Cercado", "Arce", "Gran Chaco", "Avilés", "Méndez", "O'Connor"],
        "Santa Cruz": ["Andrés Ibáñez", "Warnes", "Velasco", "Ichilo", "Chiquitos", "Sara", "Cordillera", "Vallegrande", "Florida", "Obispo Santistevan"],
        "Beni":       ["Cercado", "Vaca Díez", "General José Ballivián", "Yacuma", "Moxos", "Marbán", "Mamoré", "Iténez"],
        "Pando":      ["Nicolás Suárez", "Abuná", "Federico Román", "Madre de Dios", "Manuripi"]
    }

    ocupaciones_bolivia = [
        "Estudiante", "Agricultor/a", "Comerciante", "Ama de casa",
        "Empleado público", "Obrero/a", "Profesional independiente",
        "Transportista", "Artesano/a", "Jubilado/a", "Sin ocupación"
    ]

    # ── FILA 1 ─────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    nombre        = c1.text_input("Nombre completo",   value=st.session_state.paciente["nombre"])
    id_seguro     = c2.text_input("ID o N° de Seguro", value=st.session_state.paciente["id_seguro"])
    tipo_consulta = c3.selectbox("Tipo de Consulta", ["Institucional", "Consulta Externa"])

    # CORRECCIÓN PRINCIPAL: date_input SIN value para que empiece vacío
    # y sin intentar calcular edad hasta que el usuario seleccione una fecha
    f_nac_guardada = st.session_state.paciente.get("f_nac")
    if f_nac_guardada and isinstance(f_nac_guardada, date):
        f_nac = c4.date_input("Fecha de Nacimiento", value=f_nac_guardada,
                               format="DD/MM/YYYY",
                               min_value=date(1900, 1, 1),
                               max_value=date.today())
    else:
        f_nac = c4.date_input("Fecha de Nacimiento", value=None,
                               format="DD/MM/YYYY",
                               min_value=date(1900, 1, 1),
                               max_value=date.today())

    # ── FILA 2 ─────────────────────────────────────────────────────
    c5, c6, c7, c8 = st.columns(4)
    telefono     = c5.text_input("Teléfono / Celular",     value=st.session_state.paciente["telefono"])
    direccion    = c6.text_input("Dirección de Domicilio", value=st.session_state.paciente["direccion"])
    ocupacion    = c7.selectbox("Ocupación", ocupaciones_bolivia,
                                index=ocupaciones_bolivia.index(st.session_state.paciente["ocupacion"]))
    estado_civil = c8.selectbox("Estado Civil",
                                ["Soltero(a)", "Casado(a)", "Divorciado(a)", "Viudo(a)", "Unión libre"])

    # ── FILA 3: Edad calculada con protección contra None ──────────
    # CORRECCIÓN: solo calcula si f_nac es una fecha válida
    hoy = date.today()
    if f_nac and isinstance(f_nac, date):
        edad_calculada = hoy.year - f_nac.year - ((hoy.month, hoy.day) < (f_nac.month, f_nac.day))
        edad_texto     = calcular_edad_exacta(f_nac)
    else:
        edad_calculada = 0
        edad_texto     = "Ingrese fecha de nacimiento"

    c9, c10, c11, c12 = st.columns(4)
    c9.text_input("Edad exacta", value=edad_texto, disabled=True)
    sexo = c10.selectbox("Sexo", ["Femenino", "Masculino"],
                         index=0 if st.session_state.paciente["sexo"] == "Femenino" else 1)
    fecha_eval    = c11.date_input("Fecha de Evaluación",          format="DD/MM/YYYY")
    fecha_ingreso = c12.date_input("Fecha de Ingreso al Hospital", format="DD/MM/YYYY")

    # ── FILA 4: Procedencia ────────────────────────────────────────
    c13, c14, c15 = st.columns([1, 1, 2])
    nacionalidad  = c13.selectbox("Nacionalidad", ["Boliviana", "Extranjero"])

    if nacionalidad == "Boliviana":
        dpto      = c14.selectbox("Departamento", list(provincias_por_dpto.keys()))
        provincia = c15.selectbox("Provincia", provincias_por_dpto[dpto])
    else:
        pais   = c14.text_input("País de origen")
        region = c15.text_input("Estado/Región")

    st.markdown("---")

    if st.button("💾 Guardar Datos de Filiación"):
        if not f_nac or not isinstance(f_nac, date):
            st.error("⚠️ Ingrese la fecha de nacimiento antes de guardar.")
            return

        # Guardar en session_state["paciente"]
        st.session_state.paciente = {
            "nombre":       nombre,
            "id_seguro":    id_seguro,
            "sexo":         sexo,
            "edad":         edad_calculada,
            "f_nac":        f_nac,
            "nacionalidad": nacionalidad,
            "telefono":     telefono,
            "direccion":    direccion,
            "ocupacion":    ocupacion,
            "estado_civil": estado_civil
        }

        # Guardar también variables individuales para valoracion_nutricional.py
        st.session_state["f_nombre"]      = nombre
        st.session_state["f_sexo"]        = sexo
        st.session_state["f_edad"]        = edad_calculada
        st.session_state["f_estado_civil"]= estado_civil
        st.session_state["f_ocupacion"]   = ocupacion

        st.success(f"✅ Datos guardados — {nombre} | {edad_texto} | {sexo}")
