import streamlit as st
import pandas as pd
import plotly.express as px
import gspread

st.set_page_config(page_title="CRM BI | Consolidado", layout="wide")

# =========================================================================
# 1. SISTEMA DE SEGURIDAD Y LOGIN
# =========================================================================
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    st.markdown("<h2 style='text-align: center; color: #1c4587;'>🔒 Acceso al Sistema BI - Grupo Andrade</h2>", unsafe_allow_html=True)
    st.write("")
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        with st.form("login_form"):
            usuario = st.text_input("Usuario")
            password = st.text_input("Contraseña", type="password")
            submit = st.form_submit_button("Iniciar Sesión", use_container_width=True)
            
            if submit:
                if usuario == "CRA" and password == "CRA1234.":
                    st.session_state["autenticado"] = True
                    st.rerun()
                else:
                    st.error("❌ Usuario o contraseña incorrectos")
    
    st.stop() 

# =========================================================================
# 2. CARGA DE DATOS Y EXTRACCIÓN DE FECHAS
# =========================================================================
st.title("📊 Panel de Inteligencia Comercial y Leads")

VENDEDORES_TULTITLAN = ["AURORA", "GRACIELA", "HILDA"]

DICCIONARIO_VENDEDORES = {
    "DIEGO CORTES": "1YdiB2hYOnN6IB_GGamQw3pyXW3HZ3Yf0h20PtoQO7dI",
    "JAVIER HERNANDEZ": "1LnvTonTQpWIajhLDEF3S4okQgvxB9n_SnV3JCJcnC80",
    "JOEL CASTILLO": "14b_jY7oJIrrc4S0hsDxOamdp0SYMfcRRVm3WIbC5m8o",
    "LAURA SANCHEZ": "1IEmNudo6MZ6ijelaYbKSOE2leO_U7b5OEzdHL-AUtSw",
    "MAYRA GOMEZ": "1pyJb_U7IysUlqsRZ2fXcTBv7Jcw6_df_-_6gLurg2uo",
    "OMAR GONZALEZ": "16tehCRepOnxfAbMAOmyyS5fPkO3zK76THHsm6oNF1N8",
    "PAMELA ECHANOVE": "11rM-910TasuoGpYxbZ2ki9fEeo39zcImCqGzagI8Wbs",
    "VICTOR LOPEZ": "15KVbsq7bgATMizIALHq5R-iZnfl02si-uBBgiGEcsvU",
    "AURORA": "1e4BLDYERX4E7ILgQzaFviXCDHD9P3ayfaZteXYt8vzU",
    "GRACIELA": "1LP78iCEn7Na9iP_4DQaKVA_nNLhy8kdDBJnSgELN25Q",
    "HILDA": "1ObtW2sRdgGvyotTOvl0lEM4erASM4KyWvj1uoyOKiPk"
}

@st.cache_data(show_spinner=False)
def cargar_cartera_global():
    client = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
    
    lista_dfs = []
    barra_progreso = st.progress(0, text="Conectando con bases de asesores...")
    total_vendedores = len(DICCIONARIO_VENDEDORES)
    
    for idx, (nombre, id_archivo) in enumerate(DICCIONARIO_VENDEDORES.items()):
        try:
            hoja = client.open_by_key(id_archivo).sheet1
            datos = hoja.get_all_values()
            
            if len(datos) > 7:
                df_temporal = pd.DataFrame(datos[7:], columns=datos[6])
                
                df_temporal = df_temporal.loc[:, df_temporal.columns != ""]
                df_temporal = df_temporal.loc[:, ~df_temporal.columns.duplicated()]
                
                df_temporal.insert(0, 'ASESOR ASIGNADO', nombre)
                agencia = "CRA TULTITLAN" if nombre in VENDEDORES_TULTITLAN else "CRA CUAUTITLAN"
                df_temporal.insert(1, 'AGENCIA', agencia)
                
                lista_dfs.append(df_temporal)
                
        except Exception as e:
            st.warning(f"Error al leer {nombre} -> {repr(e)}")
            
        barra_progreso.progress((idx + 1) / total_vendedores, text=f"Descargando datos de {nombre}...")
    
    barra_progreso.empty()
    
    if lista_dfs:
        df_global = pd.concat(lista_dfs, ignore_index=True)
        if 'FECHA SOLICITUD' in df_global.columns:
            df_global = df_global[df_global['FECHA SOLICITUD'] != ""]
            
            # --- LIMPIEZA DE ESTATUS VACÍOS ---
            if 'ESTATUS' in df_global.columns:
                df_global['ESTATUS'] = df_global['ESTATUS'].replace("", "PROSPECTO SIN ATENDER")
            
            # --- MOTOR DE FECHAS PARA LOS FILTROS ---
            df_global['FECHA_DATETIME'] = pd.to_datetime(df_global['FECHA SOLICITUD'], format='%d/%m/%Y', errors='coerce')
            
            # Extraer AÑO
            df_global['AÑO'] = df_global['FECHA_DATETIME'].dt.year.fillna(0).astype(int).astype(str)
            df_global['AÑO'] = df_global['AÑO'].replace('0', 'SIN FECHA')
            
            # Extraer MES en número (para ordenar) y en Letras (para mostrar)
            df_global['MES_NUM'] = df_global['FECHA_DATETIME'].dt.month.fillna(0).astype(int)
            meses_map = {
                1: 'ENERO', 2: 'FEBRERO', 3: 'MARZO', 4: 'ABRIL',
                5: 'MAYO', 6: 'JUNIO', 7: 'JULIO', 8: 'AGOSTO',
                9: 'SEPTIEMBRE', 10: 'OCTUBRE', 11: 'NOVIEMBRE', 12: 'DICIEMBRE',
                0: 'SIN FECHA'
            }
            df_global['MES'] = df_global['MES_NUM'].map(meses_map)
            
        return df_global
    else:
        return pd.DataFrame()

with st.spinner("Descargando bases de datos (esto solo toma tiempo al iniciar sesión)..."):
    df = cargar_cartera_global()

if df.empty:
    st.error("No se extrajo ningún dato. Verifica las bases de los vendedores.")
    st.stop()

# =========================================================================
# 3. FILTROS EN MENÚS DESPLEGABLES (Expanders + Checkboxes)
# =========================================================================
st.sidebar.header("Filtros del Tablero")

if st.sidebar.button("🔄 Actualizar Leads Nuevos", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("---")

# 1. Filtro de Agencia
with st.sidebar.expander("🏢 SELECCIONA AGENCIA", expanded=False):
    agencias = ["CRA CUAUTITLAN", "CRA TULTITLAN"]
    agencias_seleccionadas = [ag for ag in agencias if st.checkbox(ag, value=True, key=f"ag_{ag}")]

df_agencia = df[df["AGENCIA"].isin(agencias_seleccionadas)]

# 2. Filtro de Año
with st.sidebar.expander("📅 SELECCIONA AÑO", expanded=False):
    anios_disp = sorted([a for a in df_agencia["AÑO"].unique() if a != 'SIN FECHA'], reverse=True)
    if 'SIN FECHA' in df_agencia["AÑO"].unique():
        anios_disp.append('SIN FECHA')
    
    anios_seleccionados = [a for a in anios_disp if st.checkbox(str(a), value=True, key=f"ano_{a}")]

df_ano = df_agencia[df_agencia["AÑO"].isin(anios_seleccionados)]

# 3. Filtro de Mes (ORDENADO CRONOLÓGICAMENTE)
with st.sidebar.expander("📆 SELECCIONA MES", expanded=False):
    # Ordenar ascendente por número de mes (1 al 12)
    meses_unicos = df_ano[["MES_NUM", "MES"]].drop_duplicates().sort_values(by="MES_NUM", ascending=True)
    meses_disp = meses_unicos["MES"].tolist()
    
    meses_seleccionados = [m for m in meses_disp if st.checkbox(m, value=True, key=f"mes_{m}")]

df_mes = df_ano[df_ano["MES"].isin(meses_seleccionados)]

# 4. Filtro de Asesor
with st.sidebar.expander("🧑‍💼 SELECCIONA ASESOR", expanded=False):
    asesores_disp = sorted(df_mes["ASESOR ASIGNADO"].unique())
    asesores_seleccionados = [as_ for as_ in asesores_disp if st.checkbox(as_, value=True, key=f"as_{as_}")]

# Matriz final ordenada para gráficos evolutivos
df_filtrado = df_mes[df_mes["ASESOR ASIGNADO"].isin(asesores_seleccionados)].sort_values(by="MES_NUM")

# =========================================================================
# 4. SISTEMA DE PESTAÑAS (TABS)
# =========================================================================
tab_general, tab_asesor = st.tabs(["📊 GENERAL (Marketing & Demanda)", "🧑‍💼 ASESOR (Rendimiento & Seguimiento)"])

# ---------------------------------------------------------
# PESTAÑA 1: GENERAL
# ---------------------------------------------------------
with tab_general:
    # KPIs Generales
    col1, col2, col3, col4 = st.columns(4)
    total_leads = len(df_filtrado)
    leads_interes = len(df_filtrado[df_filtrado["ESTATUS"] == "EN PROCESO DE TRATO"]) if "ESTATUS" in df_filtrado.columns else 0
    ventas_cerradas = len(df_filtrado[df_filtrado["ESTATUS"] == "VENTA EXITOSA"]) if "ESTATUS" in df_filtrado.columns else 0

    col1.metric("Total Leads Filtrados", total_leads)
    col2.metric("Prospectos con Interés", leads_interes)
    col3.metric("Ventas Cerradas", ventas_cerradas)
    col4.metric("Tasa de Cierre", f"{(ventas_cerradas / total_leads * 100):.1f}%" if total_leads > 0 else "0%")

    st.markdown("---")

    if total_leads > 0:
        # Fila 1 de Gráficos: Origen y Rendimiento de Anuncios
        gen_row1_col1, gen_row1_col2 = st.columns([1, 2])
        
        with gen_row1_col1:
            st.subheader("Plataforma Más Utilizada")
            if "PLATAFORMA" in df_filtrado.columns:
                fig_plat = px.pie(df_filtrado, names='PLATAFORMA', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
                st.plotly_chart(fig_plat, use_container_width=True)
                
        with gen_row1_col2:
            st.subheader("Evolución Mensual por Anuncio")
            if "ANUNCIO" in df_filtrado.columns:
                fig_ad = px.histogram(df_filtrado, x='MES', color='ANUNCIO', barmode='group', 
                                      color_discrete_sequence=px.colors.qualitative.Safe)
                fig_ad.update_layout(xaxis_title="", yaxis_title="Cantidad de Leads")
                st.plotly_chart(fig_ad, use_container_width=True)

        # Fila 2 de Gráficos: Demanda de Unidades
        st.subheader("Crecimiento de Demanda por Unidad de Interés")
        
        # Validar nombre exacto de la columna en tu base ("UNIDAD INTERES" o "UNIDAD DE INTERES")
        col_unidad = "UNIDAD DE INTERES" if "UNIDAD DE INTERES" in df_filtrado.columns else "UNIDAD INTERES"
        
        if col_unidad in df_filtrado.columns:
            fig_unidad = px.histogram(df_filtrado, x='MES', color=col_unidad, barmode='stack',
                                      color_discrete_sequence=px.colors.qualitative.Bold)
            fig_unidad.update_layout(xaxis_title="Mes", yaxis_title="Cotizaciones / Interés")
            st.plotly_chart(fig_unidad, use_container_width=True)
    else:
        st.warning("No hay registros que coincidan con los filtros seleccionados.")

# ---------------------------------------------------------
# PESTAÑA 2: ASESOR
# ---------------------------------------------------------
with tab_asesor:
    st.subheader("Nivel de Atención y Seguimiento por Asesor")
    
    if total_leads > 0 and "ESTATUS" in df_filtrado.columns:
        rendimiento = df_filtrado.groupby(['ASESOR ASIGNADO', 'ESTATUS']).size().reset_index(name='CANTIDAD')
        
        # Mapa de colores para obligar al sistema a pintar de ROJO los que no tienen atención
        mapa_colores = {
            "PROSPECTO SIN ATENDER": "#ff4b4b", # Rojo Alerta
            "EN PROCESO DE TRATO": "#3b82f6",   # Azul
            "VENTA EXITOSA": "#22c55e",         # Verde
            "YA NO TIENE INTERÉS": "#f97316",   # Naranja
            "ERROR DE CAPTURA": "#64748b"       # Gris
        }
        
        fig_asesor = px.bar(rendimiento, x='ASESOR ASIGNADO', y='CANTIDAD', color='ESTATUS', barmode='stack',
                            color_discrete_map=mapa_colores)
        fig_asesor.update_layout(xaxis_title="", yaxis_title="Leads Asignados")
        st.plotly_chart(fig_asesor, use_container_width=True)
    elif total_leads == 0:
        st.warning("Ajusta los filtros para ver el rendimiento.")

    st.markdown("---")
    st.subheader("Auditoría: Detalle de Cartera Activa")
    
    columnas_mostrar = ['AGENCIA', 'ASESOR ASIGNADO', 'FECHA SOLICITUD']
    
    # Validar qué columnas exactas existen antes de mostrarlas en la tabla
    for col in ['ANUNCIO', col_unidad if 'col_unidad' in locals() else 'UNIDAD INTERES', 'NOMBRE CLIENTE', 'ESTATUS', 'COMENTARIO ASESOR']:
        if col in df_filtrado.columns:
            columnas_mostrar.append(col)
            
    if total_leads > 0:
        st.dataframe(df_filtrado[columnas_mostrar], use_container_width=True)
