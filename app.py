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
# 2. CARGA DE DATOS Y ESTRUCTURA FIJA DE 21 COLUMNAS (A - U)
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

# Orden oficial fijo de las 21 columnas (Columna A hasta Columna U)
COLUMNAS_OFICIALES = [
    "ANUNCIO",                               # Col A (0)
    "PLATAFORMA",                            # Col B (1)
    "UNIDAD DE INTERES",                     # Col C (2)
    "NOMBRE CLIENTE",                        # Col D (3)
    "TELEFONO CLIENTE",                      # Col E (4)
    "CORREO CLIENTE",                        # Col F (5)
    "COMENTARIO CLIENTE",                    # Col G (6)
    "FECHA SOLICITUD",                       # Col H (7)
    "HORA SOLICITUD",                        # Col I (8)
    "FECHA PRIMER CONTACTO",                 # Col J (9)
    "HORA PRIMER CONTACTO",                  # Col K (10)
    "PRIMER FILTRO",                         # Col L (11)
    "UNIDAD REAL DE INTERES",                # Col M (12)
    "COMENTARIO DE ACERCAMIENTO PROSPECTO",  # Col N (13)
    "FECHA DE SEGUIMIENTO",                  # Col O (14)
    "HORA DE SEGUIMIENTO",                   # Col P (15)
    "ESTATUS PROSPECTO",                     # Col Q (16)
    "ACTIVIDAD DE SEGUIMIENTO",              # Col R (17)
    "COMENTARIO ASESOR",                     # Col S (18)
    "FECHA LÍMITE PROXIMA ACTIVIDAD",        # Col T (19)
    "DIAS TRANSCURRIDOS SIN SEGUIMIENTO"     # Col U (20)
]

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
                # Detectar dinámicamente en qué fila están los encabezados (por defecto fila 8 -> índice 7)
                inicio_datos = 8
                for i, fila in enumerate(datos[:15]):
                    fila_limpia = [str(c).strip().upper() for c in fila]
                    if "ANUNCIO" in fila_limpia or "FECHA SOLICITUD" in fila_limpia:
                        inicio_datos = i + 1
                        break
                
                filas_crudas = datos[inicio_datos:]
                if filas_crudas:
                    # Ajustar cada fila exactamente a las 21 columnas (A - U)
                    filas_normalizadas = [
                        (fila[:21] + [""] * max(0, 21 - len(fila)))
                        for fila in filas_crudas
                    ]
                    
                    df_temporal = pd.DataFrame(filas_normalizadas, columns=COLUMNAS_OFICIALES)
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
        
        # 1. Filtrar únicamente filas que tengan Fecha de Solicitud
        df_global['FECHA SOLICITUD'] = df_global['FECHA SOLICITUD'].astype(str).str.strip()
        df_global = df_global[df_global['FECHA SOLICITUD'] != ""]
        
        # 2. REGLA DE CASCADA PARA EL GRÁFICO (Col A = ANUNCIO, Col L = PRIMER FILTRO, Col Q = ESTATUS PROSPECTO)
        def regla_atencion_grafica(row):
            val_a = str(row['ANUNCIO']).strip()
            val_l = str(row['PRIMER FILTRO']).strip()
            val_q = str(row['ESTATUS PROSPECTO']).strip()
            
            if val_a != "":          # Siempre y cuando exista dato en Columna A
                if val_l == "":      # Nada en Columna L -> SIN ATENDER
                    return "SIN ATENDER"
                else:                # Sí hay algo en Columna L
                    if val_q != "":  # Si también hay algo en Columna Q -> Dejar Columna Q
                        return val_q
                    else:            # Si no hay nada en Q -> Dejar Columna L
                        return val_l
            return ""                # Si Columna A está vacía, se considera vacío
        
        df_global['ESTATUS_GRAFICO'] = df_global.apply(regla_atencion_grafica, axis=1)
        
        # 3. MOTOR DE FECHAS (Soporta formatos con o sin cero inicial, ej. 5/8/2026 o 05/08/2026)
        df_global['FECHA_DATETIME'] = pd.to_datetime(
            df_global['FECHA SOLICITUD'], dayfirst=True, format='mixed', errors='coerce'
        )
        
        # Eliminar filas cuya fecha no sea válida para evitar "SIN FECHA"
        df_global = df_global.dropna(subset=['FECHA_DATETIME'])
        
        df_global['AÑO'] = df_global['FECHA_DATETIME'].dt.year.astype(int).astype(str)
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
    st.error("No se extrajo ningún dato válido. Verifica que las hojas tengan registros con Fecha de Solicitud.")
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
    
    leads_interes = len(df_filtrado[
        (df_filtrado["PRIMER FILTRO"] == "PROSPECTO CON INTERES") |
        (df_filtrado["ESTATUS PROSPECTO"].isin(["SEGUIMIENTO", "COTIZADO", "FINANCIAMIENTO"]))
    ])
    ventas_cerradas = len(df_filtrado[df_filtrado["ESTATUS PROSPECTO"].isin(["FACTURADO", "CIERRE DE VENTA"])])

    col1.metric("Total Leads Filtrados", total_leads)
    col2.metric("Prospectos con Interés", leads_interes)
    col3.metric("Ventas Cerradas", ventas_cerradas)
    col4.metric("Tasa de Cierre", f"{(ventas_cerradas / total_leads * 100):.1f}%" if total_leads > 0 else "0%")
    st.markdown("---")

    if total_leads > 0:
        gen_row1_col1, gen_row1_col2 = st.columns([1, 2])
        with gen_row1_col1:
            st.subheader("Plataforma Más Utilizada")
            fig_plat = px.pie(df_filtrado, names='PLATAFORMA', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig_plat, use_container_width=True)
                
        with gen_row1_col2:
            st.subheader("Evolución Mensual por Anuncio")
            fig_ad = px.histogram(df_filtrado, x='MES', color='ANUNCIO', barmode='group', 
                                  color_discrete_sequence=px.colors.qualitative.Safe)
            fig_ad.update_layout(xaxis_title="", yaxis_title="Cantidad de Leads")
            st.plotly_chart(fig_ad, use_container_width=True)

        st.subheader("Crecimiento de Demanda por Unidad de Interés")
        fig_unidad = px.histogram(df_filtrado, x='MES', color="UNIDAD DE INTERES", barmode='stack',
                                  color_discrete_sequence=px.colors.qualitative.Bold)
        fig_unidad.update_layout(xaxis_title="Mes", yaxis_title="Cotizaciones / Interés")
        st.plotly_chart(fig_unidad, use_container_width=True)
    else:
        st.warning("No hay registros que coincidan con los filtros seleccionados.")

# ---------------------------------------------------------
# PESTAÑA 2: ASESOR
# ---------------------------------------------------------
with tab_asesor:
    st.subheader("Nivel de Atención y Seguimiento por Asesor dado leads activos")
    
    if total_leads > 0:
        df_grafico = df_filtrado[df_filtrado["ESTATUS_GRAFICO"] != ""]
        
        if not df_grafico.empty:
            rendimiento = df_grafico.groupby(['ASESOR ASIGNADO', 'ESTATUS_GRAFICO']).size().reset_index(name='CANTIDAD')
            
            mapa_colores_grafico = {
                "SIN ATENDER": "#ff4b4b",               # Rojo Alerta (Col A llena, Col L vacía)
                "PROSPECTO CON INTERES": "#60a5fa",     # Azul claro (Col L)
                "ERROR DE CAPTURA": "#94a3b8",          # Gris (Col L)
                "YA NO TIENE INTERES": "#f97316",       # Naranja (Col L)
                "YA NO TIENE INTERÉS": "#f97316",       # Naranja con acento
                "SIN ÉXITO DE CONTACTO": "#facc15",     # Amarillo (Col L)
                "SEGUIMIENTO": "#3b82f6",               # Azul (Col Q)
                "COTIZADO": "#818cf8",                  # Indigo (Col Q)
                "FINANCIAMIENTO": "#eab308",            # Amarillo oscuro (Col Q)
                "FACTURADO": "#22c55e",                 # Verde oscuro (Col Q)
                "CIERRE DE VENTA": "#4ade80",           # Verde claro (Col Q)
                "VENTA PERDIDA": "#ea580c",             # Naranja oscuro (Col Q)
                "COMPRA CANCELADA": "#ef4444"           # Rojo (Col Q)
            }
            
            fig_asesor = px.bar(rendimiento, x='ASESOR ASIGNADO', y='CANTIDAD', color='ESTATUS_GRAFICO', barmode='stack',
                                color_discrete_map=mapa_colores_grafico)
            fig_asesor.update_layout(xaxis_title="", yaxis_title="Leads Asignados", legend_title="Estatus de Atención")
            st.plotly_chart(fig_asesor, use_container_width=True)
        else:
            st.warning("No hay leads válidos (Columna A con datos) para graficar en este periodo.")
    else:
        st.warning("Ajusta los filtros para ver el rendimiento.")

    st.markdown("---")
    
    # ---------------------------------------------------------
    # MÓDULO: RANKING JERÁRQUICO DE ATENCIÓN
    # ---------------------------------------------------------
    st.subheader("🏆 Ranking: Nivel de Atención por Asesor")
    st.caption("Mide el porcentaje de prospectos atendidos (Columna L 'PRIMER FILTRO' capturada) sobre el total de leads asignados.")
    
    if total_leads > 0:
        df_ranking = df_filtrado.groupby('ASESOR ASIGNADO').agg(
            LEADS_ASIGNADOS=('FECHA SOLICITUD', 'count'),
            LEADS_ATENDIDOS=('PRIMER FILTRO', lambda x: (x.astype(str).str.strip() != "").sum())
        ).reset_index()
        
        df_ranking['NIVEL DE ATENCION (%)'] = (df_ranking['LEADS_ATENDIDOS'] / df_ranking['LEADS_ASIGNADOS']) * 100
        df_ranking = df_ranking.sort_values(by='NIVEL DE ATENCION (%)', ascending=False)
        
        def color_semaforo(val):
            if val >= 100:
                return 'background-color: #d9ead3; color: #274e13; font-weight: bold;' # Verde (100%)
            elif val >= 90:
                return 'background-color: #fff2cc; color: #7f6000; font-weight: bold;' # Amarillo (90% - 99%)
            else:
                return 'background-color: #f4cccc; color: #990000; font-weight: bold;' # Rojo (<= 89%)

        st.dataframe(
            df_ranking.style.map(color_semaforo, subset=['NIVEL DE ATENCION (%)']).format({'NIVEL DE ATENCION (%)': '{:.1f}%'}),
            use_container_width=True,
            hide_index=True
        )

    st.markdown("---")
    st.subheader("Auditoría: Desglose de Cartera")
    
    columnas_mostrar = [
        'AGENCIA', 'ASESOR ASIGNADO', 'FECHA SOLICITUD', 'NOMBRE CLIENTE',
        'PRIMER FILTRO', 'UNIDAD REAL DE INTERES', 'ESTATUS PROSPECTO',
        'COMENTARIO ASESOR', 'DIAS TRANSCURRIDOS SIN SEGUIMIENTO'
    ]

    # ---------------------------------------------------------
    # TABLAS DE DESGLOSE (Activa, Sin Atender, Perdida)
    # ---------------------------------------------------------
    if total_leads > 0:
        condicion_atendido = df_filtrado["PRIMER FILTRO"].astype(str).str.strip() != ""
        condicion_vacio = df_filtrado["PRIMER FILTRO"].astype(str).str.strip() == ""
        
        estatus_activos_q = ["SEGUIMIENTO", "COTIZADO", "FINANCIAMIENTO", "FACTURADO", "CIERRE DE VENTA"]
        estatus_perdidos_q = ["VENTA PERDIDA", "COMPRA CANCELADA"]
        estatus_perdidos_l = ["YA NO TIENE INTERES", "YA NO TIENE INTERÉS", "ERROR DE CAPTURA"]
        
        # 1. Cartera Activa: Atendidos que siguen con interés o en seguimiento/cierre
        df_activa = df_filtrado[
            condicion_atendido & (
                (df_filtrado["ESTATUS PROSPECTO"].isin(estatus_activos_q)) |
                ((df_filtrado["ESTATUS PROSPECTO"].astype(str).str.strip() == "") & (df_filtrado["PRIMER FILTRO"] == "PROSPECTO CON INTERES"))
            )
        ]
        
        # 2. Cartera Sin Atender: Leads asignados donde el asesor aún no llena el Primer Filtro
        df_sin_atender = df_filtrado[condicion_vacio]
        
        # 3. Cartera Perdida: Descartados en Primer Filtro o en Seguimiento
        df_perdida = df_filtrado[
            condicion_atendido & (
                (df_filtrado["PRIMER FILTRO"].isin(estatus_perdidos_l)) |
                (df_filtrado["ESTATUS PROSPECTO"].isin(estatus_perdidos_q))
            )
        ]

        st.markdown("##### 🟢 Detalle de Cartera Activa")
        st.caption("Prospectos atendidos que se mantienen con interés, en seguimiento, cotización, financiamiento o venta cerrada.")
        st.dataframe(df_activa[columnas_mostrar], use_container_width=True, hide_index=True)

        st.markdown("##### 🔴 Cartera Sin Atender")
        st.caption("Prospectos asignados donde el vendedor AÚN NO captura el Primer Filtro.")
        st.dataframe(df_sin_atender[columnas_mostrar], use_container_width=True, hide_index=True)

        st.markdown("##### 🟠 Cartera Perdida")
        st.caption("Prospectos descartados por falta de interés, error de captura, compra cancelada o venta perdida.")
        st.dataframe(df_perdida[columnas_mostrar], use_container_width=True, hide_index=True)
