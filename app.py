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
            # 1. Eliminar filas vacías o con puros espacios
            df_global = df_global[df_global['FECHA SOLICITUD'].astype(str).str.strip() != ""]
            
            # 2. LIMPIEZA DE ESTATUS VACÍOS
            if 'ESTATUS' in df_global.columns:
                df_global['ESTATUS'] = df_global['ESTATUS'].replace("", "PROSPECTO SIN ATENDER")
            
            # 3. MOTOR DE FECHAS (Forzar a datetime)
            df_global['FECHA_DATETIME'] = pd.to_datetime(df_global['FECHA SOLICITUD'], format='%d/%m/%Y', errors='coerce')
            
            # 🚀 FILTRO DESTRUCTOR: Eliminar cualquier fila que no haya arrojado una fecha válida
            df_global = df_global.dropna(subset=['FECHA_DATETIME'])
            
            # Extraer AÑO (Garantizado que es un número válido)
            df_global['AÑO'] = df_global['FECHA_DATETIME'].dt.year.astype(int).astype(str)
            
            # Extraer MES en número y texto
            df_global['MES_NUM'] = df_global['FECHA_DATETIME'].dt.month.astype(int)
            meses_map = {
                1: 'ENERO', 2: 'FEBRERO', 3: 'MARZO', 4: 'ABRIL',
                5: 'MAYO', 6: 'JUNIO', 7: 'JULIO', 8: 'AGOSTO',
                9: 'SEPTIEMBRE', 10: 'OCTUBRE', 11: 'NOVIEMBRE', 12: 'DICIEMBRE'
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
# 3. FILTROS EN MENÚS DESPLEGABLES
# =========================================================================
st.sidebar.header("Filtros del Tablero")

if st.sidebar.button("🔄 Actualizar Leads Nuevos", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("---")

with st.sidebar.expander("🏢 SELECCIONA AGENCIA", expanded=False):
    agencias = ["CRA CUAUTITLAN", "CRA TULTITLAN"]
    agencias_seleccionadas = [ag for ag in agencias if st.checkbox(ag, value=True, key=f"ag_{ag}")]

df_agencia = df[df["AGENCIA"].isin(agencias_seleccionadas)]

with st.sidebar.expander("📅 SELECCIONA AÑO", expanded=False):
    anios_disp = sorted(df_agencia["AÑO"].unique(), reverse=True)
    anios_seleccionados = [a for a in anios_disp if st.checkbox(str(a), value=True, key=f"ano_{a}")]

df_ano = df_agencia[df_agencia["AÑO"].isin(anios_seleccionados)]

with st.sidebar.expander("📆 SELECCIONA MES", expanded=False):
    meses_unicos = df_ano[["MES_NUM", "MES"]].drop_duplicates().sort_values(by="MES_NUM", ascending=True)
    meses_disp = meses_unicos["MES"].tolist()
    meses_seleccionados = [m for m in meses_disp if st.checkbox(m, value=True, key=f"mes_{m}")]

df_mes = df_ano[df_ano["MES"].isin(meses_seleccionados)]

with st.sidebar.expander("🧑‍💼 SELECCIONA ASESOR", expanded=False):
    asesores_disp = sorted(df_mes["ASESOR ASIGNADO"].unique())
    asesores_seleccionados = [as_ for as_ in asesores_disp if st.checkbox(as_, value=True, key=f"as_{as_}")]

df_filtrado = df_mes[df_mes["ASESOR ASIGNADO"].isin(asesores_seleccionados)].sort_values(by="MES_NUM")

# =========================================================================
# 4. SISTEMA DE PESTAÑAS (TABS)
# =========================================================================
tab_general, tab_asesor = st.tabs(["📊 GENERAL (Marketing & Demanda)", "🧑‍💼 ASESOR (Rendimiento & Seguimiento)"])

# ---------------------------------------------------------
# PESTAÑA 1: GENERAL
# ---------------------------------------------------------
with tab_general:
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

        st.subheader("Crecimiento de Demanda por Unidad de Interés")
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
    
    # ---------------------------------------------------------
    # MÓDULO: RANKING JERÁRQUICO DE ATENCIÓN
    # ---------------------------------------------------------
    st.subheader("🏆 Ranking: Nivel de Atención por Asesor")
    st.caption("Mide el porcentaje de prospectos que ya cuentan con un seguimiento capturado por el vendedor.")
    
    if total_leads > 0 and "COMENTARIO ASESOR" in df_filtrado.columns:
        df_ranking = df_filtrado.groupby('ASESOR ASIGNADO').agg(
            LEADS_ASIGNADOS=('FECHA SOLICITUD', 'count'),
            LEADS_ATENDIDOS=('COMENTARIO ASESOR', lambda x: (x.astype(str).str.strip() != "").sum())
        ).reset_index()
        
        df_ranking['NIVEL DE ATENCION (%)'] = (df_ranking['LEADS_ATENDIDOS'] / df_ranking['LEADS_ASIGNADOS']) * 100
        df_ranking = df_ranking.sort_values(by='NIVEL DE ATENCION (%)', ascending=False)
        
        def color_semaforo(val):
            if val == 100:
                return 'background-color: #d9ead3; color: #274e13; font-weight: bold;' # Verde
            elif val >= 90:
                return 'background-color: #fff2cc; color: #7f6000; font-weight: bold;' # Amarillo
            else:
                return 'background-color: #f4cccc; color: #990000; font-weight: bold;' # Rojo

        st.dataframe(
            df_ranking.style.map(color_semaforo, subset=['NIVEL DE ATENCION (%)']).format({'NIVEL DE ATENCION (%)': '{:.1f}%'}),
            use_container_width=True,
            hide_index=True
        )

    st.markdown("---")
    st.subheader("Auditoría: Desglose de Cartera")
    
    columnas_mostrar = ['AGENCIA', 'ASESOR ASIGNADO', 'FECHA SOLICITUD']
    col_unidad_real = col_unidad if 'col_unidad' in locals() else 'UNIDAD INTERES'
    
    for col in ['ANUNCIO', col_unidad_real, 'NOMBRE CLIENTE', 'ESTATUS', 'COMENTARIO ASESOR']:
        if col in df_filtrado.columns:
            columnas_mostrar.append(col)

    # ---------------------------------------------------------
    # TABLAS DE DESGLOSE (Activa, Sin Atender, Perdida)
    # ---------------------------------------------------------
    if total_leads > 0 and "COMENTARIO ASESOR" in df_filtrado.columns:
        
        condicion_comentario_lleno = df_filtrado["COMENTARIO ASESOR"].astype(str).str.strip() != ""
        condicion_comentario_vacio = df_filtrado["COMENTARIO ASESOR"].astype(str).str.strip() == ""
        
        df_activa = df_filtrado[condicion_comentario_lleno & (df_filtrado["ESTATUS"].isin(["EN PROCESO DE TRATO", "VENTA EXITOSA"]))]
        df_sin_atender = df_filtrado[condicion_comentario_vacio]
        df_perdida = df_filtrado[condicion_comentario_lleno & (df_filtrado["ESTATUS"] == "YA NO TIENE INTERÉS")]

        st.markdown("##### 🟢 Detalle de Cartera Activa")
        st.caption("Prospectos que ya fueron atendidos (tienen comentario) y se mantienen en trato o se cerró la venta.")
        st.dataframe(df_activa[columnas_mostrar], use_container_width=True, hide_index=True)

        st.markdown("##### 🔴 Cartera Sin Atender")
        st.caption("Prospectos que cayeron a la base pero el vendedor AÚN NO captura ningún comentario.")
        st.dataframe(df_sin_atender[columnas_mostrar], use_container_width=True, hide_index=True)

        st.markdown("##### 🟠 Cartera Perdida")
        st.caption("Prospectos descartados tras la atención del vendedor.")
        st.dataframe(df_perdida[columnas_mostrar], use_container_width=True, hide_index=True)
