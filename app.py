import streamlit as st
import pandas as pd
import plotly.express as px
import gspread

st.set_page_config(page_title="CRM BI | Consolidado", layout="wide")
st.title("📊 Panel de Inteligencia Comercial y Leads")

# Diccionario maestro unificado (Cuautitlán + Tultitlán)
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

def cargar_cartera_global():
    # Conexión oficial y directa de gspread usando los secretos de Streamlit
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
                df_temporal.insert(0, 'ASESOR ASIGNADO', nombre)
                lista_dfs.append(df_temporal)
                
        except Exception as e:
            st.warning(f"Error al leer {nombre} -> {repr(e)}")
            
        barra_progreso.progress((idx + 1) / total_vendedores, text=f"Descargando datos de {nombre}...")
    
    barra_progreso.empty()
    
    if lista_dfs:
        df_global = pd.concat(lista_dfs, ignore_index=True)
        if 'FECHA SOLICITUD' in df_global.columns:
            df_global = df_global[df_global['FECHA SOLICITUD'] != ""]
        return df_global
    else:
        return pd.DataFrame()

df = cargar_cartera_global()

if df.empty:
    st.error("No se extrajo ningún dato. Verifica que la API de Google Sheets esté habilitada en Google Cloud.")
    st.stop()

# --- FILTROS LATERALES ---
st.sidebar.header("Filtros")
asesor_filtro = st.sidebar.multiselect("Asesor", options=df["ASESOR ASIGNADO"].unique(), default=df["ASESOR ASIGNADO"].unique())

if "PLATAFORMA" in df.columns:
    plataforma_filtro = st.sidebar.multiselect("Plataforma", options=df["PLATAFORMA"].unique(), default=df["PLATAFORMA"].unique())
    df_filtrado = df[(df["ASESOR ASIGNADO"].isin(asesor_filtro)) & (df["PLATAFORMA"].isin(plataforma_filtro))]
else:
    df_filtrado = df[df["ASESOR ASIGNADO"].isin(asesor_filtro)]

# --- KPIs PRINCIPALES ---
col1, col2, col3, col4 = st.columns(4)
total_leads = len(df_filtrado)

leads_interes = 0
ventas_cerradas = 0

if "PRIMER FILTRO" in df_filtrado.columns:
    leads_interes = len(df_filtrado[df_filtrado["PRIMER FILTRO"] == "PROSPECTO CON INTERES"])

if "ESTATUS PROSPECTO" in df_filtrado.columns:
    ventas_cerradas = len(df_filtrado[df_filtrado["ESTATUS PROSPECTO"].isin(["CIERRE DE VENTA", "FACTURADO"])])

col1.metric("Total Leads Asignados", total_leads)
col2.metric("Prospectos con Interés", leads_interes)
col3.metric("Ventas Cerradas", ventas_cerradas)
col4.metric("Tasa de Cierre", f"{(ventas_cerradas / total_leads * 100):.1f}%" if total_leads > 0 else "0%")

st.markdown("---")

# --- GRÁFICOS BI ---
row1_col1, row1_col2 = st.columns(2)

with row1_col1:
    st.subheader("Tráfico por Plataforma")
    if "PLATAFORMA" in df_filtrado.columns:
        fig_plat = px.pie(df_filtrado, names='PLATAFORMA', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig_plat, use_container_width=True)
    else:
        st.info("Columna PLATAFORMA no encontrada en la base.")

with row1_col2:
    st.subheader("Rendimiento por Asesor")
    if "PRIMER FILTRO" in df_filtrado.columns:
        rendimiento = df_filtrado.groupby(['ASESOR ASIGNADO', 'PRIMER FILTRO']).size().reset_index(name='CANTIDAD')
        fig_asesor = px.bar(rendimiento, x='ASESOR ASIGNADO', y='CANTIDAD', color='PRIMER FILTRO', barmode='stack')
        st.plotly_chart(fig_asesor, use_container_width=True)
    else:
        st.info("Columna PRIMER FILTRO no encontrada en la base.")

st.subheader("Detalle de Cartera Activa")
columnas_mostrar = ['ASESOR ASIGNADO']
for col in ['FECHA SOLICITUD', 'ANUNCIO', 'NOMBRE CLIENTE', 'PRIMER FILTRO', 'ESTATUS PROSPECTO']:
    if col in df_filtrado.columns:
        columnas_mostrar.append(col)
        
st.dataframe(df_filtrado[columnas_mostrar], use_container_width=True)
