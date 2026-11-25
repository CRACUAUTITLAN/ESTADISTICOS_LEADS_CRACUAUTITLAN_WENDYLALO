import time
import gspread
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="CRM BI | Consolidado", layout="wide")

# =========================================================================
# 1. SISTEMA DE SEGURIDAD Y LOGIN
# =========================================================================
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    st.markdown(
        "<h2 style='text-align: center; color: #1c4587;'>🔒 Acceso al Sistema"
        " BI - Grupo Andrade</h2>",
        unsafe_allow_html=True,
    )
    st.write("")

    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        with st.form("login_form"):
            usuario = st.text_input("Usuario")
            password = st.text_input("Contraseña", type="password")
            submit = st.form_submit_button(
                "Iniciar Sesión", use_container_width=True
            )

            if submit:
                if usuario == "CRA" and password == "CRA1234.":
                    st.session_state["autenticado"] = True
                    st.rerun()
                else:
                    st.error("❌ Usuario o contraseña incorrectos")

    st.stop()

# =========================================================================
# 2. CARGA DE DATOS Y DICCIONARIO ACTUALIZADO (14 ASESORES)
# =========================================================================
st.title("📊 Panel de Inteligencia Comercial y Leads")

VENDEDORES_TULTITLAN = [
    "AURORA GONZALEZ",
    "GRACIELA VELEZ",
    "HILDA OROZCO",
    "LUIS MARTINEZ",
    "MAURICIO PEREZ",
]

DICCIONARIO_VENDEDORES = {
    # CRA CUAUTITLÁN (9 Asesores)
    "DIEGO CORTES": "1YdiB2hYOnN6IB_GGamQw3pyXW3HZ3Yf0h20PtoQO7dI",
    "JAVIER HERNANDEZ": "1LnvTonTQpWIajhLDEF3S4okQgvxB9n_SnV3JCJcnC80",
    "JOEL CASTILLO": "14b_jY7oJIrrc4S0hsDxOamdp0SYMfcRRVm3WIbC5m8o",
    "LAURA SANCHEZ": "1IEmNudo6MZ6ijelaYbKSOE2leO_U7b5OEzdHL-AUtSw",
    "MAYRA GOMEZ": "1pyJb_U7IysUlqsRZ2fXcTBv7Jcw6_df_-_6gLurg2uo",
    "OMAR GONZALEZ": "16tehCRepOnxfAbMAOmyyS5fPkO3zK76THHsm6oNF1N8",
    "PAMELA ECHANOVE": "11rM-910TasuoGpYxbZ2ki9fEeo39zcImCqGzagI8Wbs",
    "VICTOR LOPEZ": "15KVbsq7bgATMizIALHq5R-iZnfl02si-uBBgiGEcsvU",
    "GUILLERMO URIBE": "1hSURRdqGrPhmJaYnKL_D8_QAcvupqxGA5xiRDO2FZ-Q",
    # CRA TULTITLÁN (5 Asesores)
    "AURORA GONZALEZ": "1e4BLDYERX4E7ILgQzaFviXCDHD9P3ayfaZteXYt8vzU",
    "GRACIELA VELEZ": "1LP78iCEn7Na9iP_4DQaKVA_nNLhy8kdDBJnSgELN25Q",
    "HILDA OROZCO": "1ObtW2sRdgGvyotTOvl0lEM4erASM4KyWvj1uoyOKiPk",
    "LUIS MARTINEZ": "1A3C0ir2rwNqT557ZFKWUvknuZUJ8kwlybbsbmqAnTro",
    "MAURICIO PEREZ": "1MP1a0KwzChKD51FQ6w_wgdbNdzAAvD8yRBstyNJXhqY",
}

COLUMNAS_OFICIALES = [
    "ANUNCIO",  # Col A (0)
    "PLATAFORMA",  # Col B (1)
    "UNIDAD DE INTERES",  # Col C (2)
    "NOMBRE CLIENTE",  # Col D (3)
    "TELEFONO CLIENTE",  # Col E (4)
    "CORREO CLIENTE",  # Col F (5)
    "COMENTARIO CLIENTE",  # Col G (6)
    "FECHA SOLICITUD",  # Col H (7)
    "HORA SOLICITUD",  # Col I (8)
    "FECHA PRIMER CONTACTO",  # Col J (9)
    "HORA PRIMER CONTACTO",  # Col K (10)
    "PRIMER FILTRO",  # Col L (11)
    "UNIDAD REAL DE INTERES",  # Col M (12)
    "COMENTARIO DE ACERCAMIENTO PROSPECTO",  # Col N (13)
    "FECHA DE SEGUIMIENTO",  # Col O (14)
    "HORA DE SEGUIMIENTO",  # Col P (15)
    "ESTATUS PROSPECTO",  # Col Q (16)
    "ACTIVIDAD DE SEGUIMIENTO",  # Col R (17)
    "COMENTARIO ASESOR",  # Col S (18)
    "FECHA LÍMITE PROXIMA ACTIVIDAD",  # Col T (19)
    "DIAS TRANSCURRIDOS SIN SEGUIMIENTO",  # Col U (20)
]


@st.cache_data(show_spinner=False)
def cargar_cartera_global():
    client = gspread.service_account_from_dict(
        st.secrets["gcp_service_account"]
    )

    lista_dfs = []
    barra_progreso = st.progress(0, text="Conectando con bases de asesores...")
    total_vendedores = len(DICCIONARIO_VENDEDORES)

    for idx, (nombre, id_archivo) in enumerate(DICCIONARIO_VENDEDORES.items()):
        try:
            hoja = client.open_by_key(id_archivo).sheet1
            datos = hoja.get_all_values()

            if len(datos) > 7:
                inicio_datos = 8
                for i, fila in enumerate(datos[:15]):
                    fila_limpia = [str(c).strip().upper() for c in fila]
                    if (
                        "ANUNCIO" in fila_limpia
                        or "FECHA SOLICITUD" in fila_limpia
                    ):
                        inicio_datos = i + 1
                        break

                filas_crudas = datos[inicio_datos:]
                if filas_crudas:
                    filas_normalizadas = [
                        (fila[:21] + [""] * max(0, 21 - len(fila)))
                        for fila in filas_crudas
                    ]

                    df_temporal = pd.DataFrame(
                        filas_normalizadas, columns=COLUMNAS_OFICIALES
                    )
                    df_temporal.insert(0, "ASESOR ASIGNADO", nombre)
                    agencia = (
                        "CRA TULTITLAN"
                        if nombre in VENDEDORES_TULTITLAN
                        else "CRA CUAUTITLAN"
                    )
                    df_temporal.insert(1, "AGENCIA", agencia)

                    lista_dfs.append(df_temporal)

        except Exception as e:
            st.warning(f"Error al leer {nombre} -> {repr(e)}")

        barra_progreso.progress(
            (idx + 1) / total_vendedores,
            text=f"Descargando datos de {nombre}...",
        )
        # Pausa preventiva para respetar el límite de lecturas por minuto de Google Sheets API
        time.sleep(1.1)

    barra_progreso.empty()

    if lista_dfs:
        df_global = pd.concat(lista_dfs, ignore_index=True)

        # Limpiar espacios en columnas clave
        for col_limpiar in [
            "FECHA SOLICITUD",
            "NOMBRE CLIENTE",
            "FECHA PRIMER CONTACTO",
            "PRIMER FILTRO",
            "FECHA DE SEGUIMIENTO",
            "ESTATUS PROSPECTO",
            "DIAS TRANSCURRIDOS SIN SEGUIMIENTO",
        ]:
            df_global[col_limpiar] = (
                df_global[col_limpiar].astype(str).str.strip()
            )

        # Conservar únicamente filas con Fecha de Solicitud válida
        df_global = df_global[df_global["FECHA SOLICITUD"] != ""]

        # Motor de fechas principales (Columna H)
        df_global["FECHA_DATETIME"] = pd.to_datetime(
            df_global["FECHA SOLICITUD"],
            dayfirst=True,
            format="mixed",
            errors="coerce",
        )
        df_global = df_global.dropna(subset=["FECHA_DATETIME"])

        # Motor de fecha primer contacto (Columna J) para calcular J - H
        df_global["FECHA_1ER_CONTACTO_DT"] = pd.to_datetime(
            df_global["FECHA PRIMER CONTACTO"],
            dayfirst=True,
            format="mixed",
            errors="coerce",
        )
        df_global["DIAS_1ER_CONTACTO"] = (
            df_global["FECHA_1ER_CONTACTO_DT"] - df_global["FECHA_DATETIME"]
        ).dt.days
        # Evitar días negativos por capturas el mismo día con diferencia de zona horaria
        df_global["DIAS_1ER_CONTACTO"] = df_global["DIAS_1ER_CONTACTO"].apply(
            lambda x: max(0, x) if pd.notnull(x) else np.nan
        )

        # Evaluación de Columna U para el gráfico de Nivel de Atención
        def clasificar_atencion_u(row):
            cliente = row["NOMBRE CLIENTE"]
            val_u = row["DIAS TRANSCURRIDOS SIN SEGUIMIENTO"]

            if cliente == "":
                return ""
            try:
                num_u = float(val_u)
                if num_u < 0:
                    return "EN SEGUIMIENTO"
                else:
                    return "SIN ATENDER / SEGUIMIENTO PENDIENTE"
            except ValueError:
                # Si Columna U está vacía (lead sin fecha límite asignada) o dice COMPLETADO
                if val_u.upper() == "COMPLETADO":
                    return "EN SEGUIMIENTO"
                return "SIN ATENDER / SEGUIMIENTO PENDIENTE"

        df_global["ESTATUS_GRAFICO_U"] = df_global.apply(
            clasificar_atencion_u, axis=1
        )

        # Extraer Año y Mes
        df_global["AÑO"] = (
            df_global["FECHA_DATETIME"].dt.year.astype(int).astype(str)
        )
        df_global["MES_NUM"] = df_global["FECHA_DATETIME"].dt.month.astype(int)
        meses_map = {
            1: "ENERO",
            2: "FEBRERO",
            3: "MARZO",
            4: "ABRIL",
            5: "MAYO",
            6: "JUNIO",
            7: "JULIO",
            8: "AGOSTO",
            9: "SEPTIEMBRE",
            10: "OCTUBRE",
            11: "NOVIEMBRE",
            12: "DICIEMBRE",
        }
        df_global["MES"] = df_global["MES_NUM"].map(meses_map)

        return df_global
    else:
        return pd.DataFrame()


with st.spinner(
    "Descargando bases de datos (esto solo toma tiempo al iniciar sesión)..."
):
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
    agencias_seleccionadas = [
        ag for ag in agencias if st.checkbox(ag, value=True, key=f"ag_{ag}")
    ]

df_agencia = df[df["AGENCIA"].isin(agencias_seleccionadas)]

with st.sidebar.expander("📅 SELECCIONA AÑO", expanded=False):
    anios_disp = sorted(df_agencia["AÑO"].unique(), reverse=True)
    anios_seleccionados = [
        a for a in anios_disp if st.checkbox(str(a), value=True, key=f"ano_{a}")
    ]

df_ano = df_agencia[df_agencia["AÑO"].isin(anios_seleccionados)]

with st.sidebar.expander("📆 SELECCIONA MES", expanded=False):
    meses_unicos = (
        df_ano[["MES_NUM", "MES"]]
        .drop_duplicates()
        .sort_values(by="MES_NUM", ascending=True)
    )
    meses_disp = meses_unicos["MES"].tolist()
    meses_seleccionados = [
        m for m in meses_disp if st.checkbox(m, value=True, key=f"mes_{m}")
    ]

df_mes = df_ano[df_ano["MES"].isin(meses_seleccionados)]

with st.sidebar.expander("🧑‍💼 SELECCIONA ASESOR", expanded=False):
    asesores_disp = sorted(df_mes["ASESOR ASIGNADO"].unique())
    asesores_seleccionados = [
        as_
        for as_ in asesores_disp
        if st.checkbox(as_, value=True, key=f"as_{as_}")
    ]

df_filtrado = df_mes[
    df_mes["ASESOR ASIGNADO"].isin(asesores_seleccionados)
].sort_values(by="MES_NUM")

# =========================================================================
# 4. SISTEMA DE PESTAÑAS (TABS)
# =========================================================================
tab_general, tab_asesor = st.tabs([
    "📊 GENERAL (Marketing & Demanda)",
    "🧑‍💼 ASESOR (Rendimiento & Seguimiento)",
])

# ---------------------------------------------------------
# PESTAÑA 1: GENERAL
# ---------------------------------------------------------
with tab_general:
    col1, col2, col3, col4 = st.columns(4)
    total_leads = len(df_filtrado)

    leads_interes = len(
        df_filtrado[
            (df_filtrado["PRIMER FILTRO"] == "PROSPECTO CON INTERES")
            | (
                df_filtrado["ESTATUS PROSPECTO"].isin(
                    ["SEGUIMIENTO", "COTIZADO", "FINANCIAMIENTO"]
                )
            )
        ]
    )
    ventas_cerradas = len(
        df_filtrado[
            df_filtrado["ESTATUS PROSPECTO"].isin(
                ["FACTURADO", "CIERRE DE VENTA"]
            )
        ]
    )

    col1.metric("Total Leads Filtrados", total_leads)
    col2.metric("Prospectos Activos", leads_interes)
    col3.metric("Ventas Cerradas", ventas_cerradas)
    col4.metric(
        "Tasa de Cierre",
        f"{(ventas_cerradas / total_leads * 100):.1f}%"
        if total_leads > 0
        else "0%",
    )
    st.markdown("---")

    if total_leads > 0:
        gen_row1_col1, gen_row1_col2 = st.columns([1, 2])
        with gen_row1_col1:
            st.subheader("Plataforma Más Utilizada")
            fig_plat = px.pie(
                df_filtrado,
                names="PLATAFORMA",
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Pastel,
            )
            st.plotly_chart(fig_plat, use_container_width=True)

        with gen_row1_col2:
            st.subheader("Evolución Mensual por Anuncio")
            fig_ad = px.histogram(
                df_filtrado,
                x="MES",
                color="ANUNCIO",
                barmode="group",
                color_discrete_sequence=px.colors.qualitative.Safe,
            )
            fig_ad.update_layout(
                xaxis_title="", yaxis_title="Cantidad de Leads"
            )
            st.plotly_chart(fig_ad, use_container_width=True)

        st.subheader("Crecimiento de Demanda por Unidad de Interés")
        fig_unidad = px.histogram(
            df_filtrado,
            x="MES",
            color="UNIDAD DE INTERES",
            barmode="stack",
            color_discrete_sequence=px.colors.qualitative.Bold,
        )
        fig_unidad.update_layout(
            xaxis_title="Mes", yaxis_title="Cotizaciones / Interés"
        )
        st.plotly_chart(fig_unidad, use_container_width=True)
    else:
        st.warning("No hay registros que coincidan con los filtros seleccionados.")

# ---------------------------------------------------------
# PESTAÑA 2: ASESOR
# ---------------------------------------------------------
with tab_asesor:
    # Filtrar únicamente filas donde exista nombre de cliente en Columna D
    df_validos_d = df_filtrado[df_filtrado["NOMBRE CLIENTE"] != ""].copy()

    if not df_validos_d.empty:
        # =====================================================================
        # TABLA 1: RESUMEN POR AGENCIA
        # =====================================================================
        st.subheader("📋 RESUMEN POR AGENCIA")

        filas_resumen = []
        # Iterar sobre los asesores seleccionados en los filtros
        for asesor in sorted(df_validos_d["ASESOR ASIGNADO"].unique()):
            sub = df_validos_d[df_validos_d["ASESOR ASIGNADO"] == asesor]
            agencia_val = (
                "CRA TULTI" if asesor in VENDEDORES_TULTITLAN else "CRA CUAUTI"
            )

            num_prospectos = len(sub)
            primer_acercamiento = (sub["FECHA PRIMER CONTACTO"] != "").sum()
            pct_primer = (
                (primer_acercamiento / num_prospectos * 100)
                if num_prospectos > 0
                else 0.0
            )

            seguimiento = (sub["FECHA DE SEGUIMIENTO"] != "").sum()
            pct_seguimiento = (
                (seguimiento / num_prospectos * 100)
                if num_prospectos > 0
                else 0.0
            )

            promedio_pct = (pct_primer + pct_seguimiento) / 2.0
            dias_prom_1er = sub["DIAS_1ER_CONTACTO"].mean()

            filas_resumen.append({
                "AGENCIA": agencia_val,
                "ASESOR / EJECUTIVO": asesor,
                "NÚMERO DE PROSPECTOS": num_prospectos,
                "PRIMER ACERCAMIENTO": primer_acercamiento,
                "% PRIMER ACERCAMIENTO": pct_primer,
                "SEGUIMIENTO": seguimiento,
                "% SEGUIMIENTO": pct_seguimiento,
                "PROMEDIO (%)": promedio_pct,
                "DÍAS PROM. 1ER CONTACTO": (
                    dias_prom_1er if pd.notnull(dias_prom_1er) else 0.0
                ),
            })

        df_resumen = pd.DataFrame(filas_resumen)

        # Calcular filas de PROMEDIO POR ASESOR y TOTAL CONSOLIDADO
        prom_prospectos = df_resumen["NÚMERO DE PROSPECTOS"].mean()
        prom_1er_acerc = df_resumen["PRIMER ACERCAMIENTO"].mean()
        prom_pct_1er = df_resumen["% PRIMER ACERCAMIENTO"].mean()
        prom_seg = df_resumen["SEGUIMIENTO"].mean()
        prom_pct_seg = df_resumen["% SEGUIMIENTO"].mean()
        prom_general_pct = df_resumen["PROMEDIO (%)"].mean()
        prom_dias_asesor = df_resumen["DÍAS PROM. 1ER CONTACTO"].mean()

        tot_prospectos = df_resumen["NÚMERO DE PROSPECTOS"].sum()
        tot_1er_acerc = df_resumen["PRIMER ACERCAMIENTO"].sum()
        tot_pct_1er = (
            (tot_1er_acerc / tot_prospectos * 100) if tot_prospectos > 0 else 0.0
        )
        tot_seg = df_resumen["SEGUIMIENTO"].sum()
        tot_pct_seg = (
            (tot_seg / tot_prospectos * 100) if tot_prospectos > 0 else 0.0
        )
        tot_general_pct = (tot_pct_1er + tot_pct_seg) / 2.0
        tot_dias_global = df_validos_d["DIAS_1ER_CONTACTO"].mean()

        fila_promedio = pd.DataFrame([{
            "AGENCIA": "PROMEDIO",
            "ASESOR / EJECUTIVO": "PROMEDIO POR ASESOR",
            "NÚMERO DE PROSPECTOS": round(prom_prospectos, 1),
            "PRIMER ACERCAMIENTO": round(prom_1er_acerc, 1),
            "% PRIMER ACERCAMIENTO": prom_pct_1er,
            "SEGUIMIENTO": round(prom_seg, 1),
            "% SEGUIMIENTO": prom_pct_seg,
            "PROMEDIO (%)": prom_general_pct,
            "DÍAS PROM. 1ER CONTACTO": round(prom_dias_asesor, 1),
        }])

        fila_total = pd.DataFrame([{
            "AGENCIA": "TOTAL",
            "ASESOR / EJECUTIVO": "TOTAL CONSOLIDADO",
            "NÚMERO DE PROSPECTOS": int(tot_prospectos),
            "PRIMER ACERCAMIENTO": int(tot_1er_acerc),
            "% PRIMER ACERCAMIENTO": tot_pct_1er,
            "SEGUIMIENTO": int(tot_seg),
            "% SEGUIMIENTO": tot_pct_seg,
            "PROMEDIO (%)": tot_general_pct,
            "DÍAS PROM. 1ER CONTACTO": (
                round(tot_dias_global, 1) if pd.notnull(tot_dias_global) else 0.0
            ),
        }])

        df_resumen_final = pd.concat(
            [df_resumen, fila_promedio, fila_total], ignore_index=True
        )

        # Estilizado de colores tipo semáforo y filas resumen
        def estilo_resumen(row):
            estilos = [""] * len(row)
            if row["AGENCIA"] == "PROMEDIO":
                return [
                    "background-color: #f3f4f6; color: #111827; font-weight:"
                    " bold;"
                ] * len(row)
            if row["AGENCIA"] == "TOTAL":
                return [
                    "background-color: #111827; color: #ffffff; font-weight:"
                    " bold;"
                ] * len(row)

            cols_pct = [
                "% PRIMER ACERCAMIENTO",
                "% SEGUIMIENTO",
                "PROMEDIO (%)",
            ]
            for i, col_name in enumerate(row.index):
                if col_name in cols_pct:
                    val = row[col_name]
                    if val >= 100:
                        estilos[i] = (
                            "background-color: #d9ead3; color: #274e13;"
                            " font-weight: bold;"
                        )
                    elif val >= 75:
                        estilos[i] = (
                            "background-color: #fff2cc; color: #7f6000;"
                            " font-weight: bold;"
                        )
                    else:
                        estilos[i] = (
                            "background-color: #f4cccc; color: #990000;"
                            " font-weight: bold;"
                        )
            return estilos

        st.dataframe(
            df_resumen_final.style.apply(estilo_resumen, axis=1).format({
                "NÚMERO DE PROSPECTOS": "{:g}",
                "PRIMER ACERCAMIENTO": "{:g}",
                "% PRIMER ACERCAMIENTO": "{:.1f}%",
                "SEGUIMIENTO": "{:g}",
                "% SEGUIMIENTO": "{:.1f}%",
                "PROMEDIO (%)": "{:.1f}%",
                "DÍAS PROM. 1ER CONTACTO": "{:.1f}",
            }),
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("---")

        # =====================================================================
        # TABLA 2: RESULTADOS DE PRIMER CONTACTO Y ESTATUS DEL SEGUIMIENTO
        # =====================================================================
        st.subheader(
            "📊 RESULTADOS DE PRIMER CONTACTO Y ESTATUS DEL SEGUIMIENTO"
        )

        filas_resultados = []
        for asesor in sorted(df_validos_d["ASESOR ASIGNADO"].unique()):
            sub = df_validos_d[df_validos_d["ASESOR ASIGNADO"] == asesor]

            pf_col = sub["PRIMER FILTRO"].str.upper()
            ep_col = sub["ESTATUS PROSPECTO"].str.upper()

            total_primer_filtro = (pf_col != "").sum()
            prospecto_interes = (pf_col == "PROSPECTO CON INTERES").sum()
            sin_exito = (
                pf_col.isin(["SIN ÉXITO DE CONTACTO", "SIN EXITO DE CONTACTO"])
            ).sum()
            pendiente_1er = (pf_col == "").sum()

            en_seguimiento = (ep_col == "SEGUIMIENTO").sum()
            cotizado = (ep_col == "COTIZADO").sum()
            financiamiento = (ep_col == "FINANCIAMIENTO").sum()
            facturado = (
                ep_col.isin(["FACTURADO", "CIERRE DE VENTA"])
            ).sum()
            sin_seguimiento = (
                (pf_col != "") & (ep_col == "")
            ).sum()

            filas_resultados.append({
                "ASESOR / EJECUTIVO": asesor,
                "PRIMER FILTRO": int(total_primer_filtro),
                "PROSPECTO CON INTERÉS": int(prospecto_interes),
                "SIN ÉXITO DE CONTACTO": int(sin_exito),
                "PENDIENTE 1ER CONTACTO": int(pendiente_1er),
                "EN SEGUIMIENTO": int(en_seguimiento),
                "COTIZADO": int(cotizado),
                "FINANCIAMIENTO": int(financiamiento),
                "FACTURADO": int(facturado),
                "SIN SEGUIMIENTO": int(sin_seguimiento),
            })

        df_resultados = pd.DataFrame(filas_resultados)

        fila_total_res = pd.DataFrame([{
            "ASESOR / EJECUTIVO": "TOTAL GENERAL",
            "PRIMER FILTRO": int(df_resultados["PRIMER FILTRO"].sum()),
            "PROSPECTO CON INTERÉS": int(
                df_resultados["PROSPECTO CON INTERÉS"].sum()
            ),
            "SIN ÉXITO DE CONTACTO": int(
                df_resultados["SIN ÉXITO DE CONTACTO"].sum()
            ),
            "PENDIENTE 1ER CONTACTO": int(
                df_resultados["PENDIENTE 1ER CONTACTO"].sum()
            ),
            "EN SEGUIMIENTO": int(df_resultados["EN SEGUIMIENTO"].sum()),
            "COTIZADO": int(df_resultados["COTIZADO"].sum()),
            "FINANCIAMIENTO": int(df_resultados["FINANCIAMIENTO"].sum()),
            "FACTURADO": int(df_resultados["FACTURADO"].sum()),
            "SIN SEGUIMIENTO": int(df_resultados["SIN SEGUIMIENTO"].sum()),
        }])

        df_resultados_final = pd.concat(
            [df_resultados, fila_total_res], ignore_index=True
        )

        def estilo_resultados(row):
            if row["ASESOR / EJECUTIVO"] == "TOTAL GENERAL":
                return [
                    "background-color: #111827; color: #ffffff; font-weight:"
                    " bold;"
                ] * len(row)
            return [""] * len(row)

        st.dataframe(
            df_resultados_final.style.apply(estilo_resultados, axis=1),
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("---")

        # =====================================================================
        # GRÁFICO: NIVEL DE ATENCIÓN Y SEGUIMIENTO (COLUMNA U)
        # =====================================================================
        st.subheader(
            "Nivel de Atención y Seguimiento por Asesor dado leads activos"
        )

        df_grafico = df_validos_d[df_validos_d["ESTATUS_GRAFICO_U"] != ""]
        if not df_grafico.empty:
            rendimiento = (
                df_grafico.groupby(["ASESOR ASIGNADO", "ESTATUS_GRAFICO_U"])
                .size()
                .reset_index(name="CANTIDAD")
            )

            mapa_colores_u = {
                "EN SEGUIMIENTO": "#22c55e",  # Verde (Columna U < 0)
                "SIN ATENDER / SEGUIMIENTO PENDIENTE": "#ff4b4b",  # Rojo (Columna U >= 0)
            }

            fig_asesor = px.bar(
                rendimiento,
                x="ASESOR ASIGNADO",
                y="CANTIDAD",
                color="ESTATUS_GRAFICO_U",
                barmode="stack",
                color_discrete_map=mapa_colores_u,
            )
            fig_asesor.update_layout(
                xaxis_title="",
                yaxis_title="Leads Activos",
                legend_title="Estatus (Columna U)",
            )
            st.plotly_chart(fig_asesor, use_container_width=True)

        st.markdown("---")

        # =====================================================================
        # RANKING JERÁRQUICO DE ATENCIÓN
        # =====================================================================
        st.subheader("🏆 Ranking: Nivel de Atención por Asesor")
        st.caption(
            "Mide el porcentaje de prospectos atendidos (Columna L 'PRIMER"
            " FILTRO' capturada) sobre el total de leads asignados."
        )

        df_ranking = (
            df_validos_d.groupby("ASESOR ASIGNADO")
            .agg(
                LEADS_ASIGNADOS=("NOMBRE CLIENTE", "count"),
                LEADS_ATENDIDOS=(
                    "PRIMER FILTRO",
                    lambda x: (x.astype(str).str.strip() != "").sum(),
                ),
            )
            .reset_index()
        )

        df_ranking["NIVEL DE ATENCION (%)"] = (
            df_ranking["LEADS_ATENDIDOS"] / df_ranking["LEADS_ASIGNADOS"]
        ) * 100
        df_ranking = df_ranking.sort_values(
            by="NIVEL DE ATENCION (%)", ascending=False
        )

        def color_semaforo(val):
            if val >= 100:
                return (
                    "background-color: #d9ead3; color: #274e13; font-weight:"
                    " bold;"
                )
            elif val >= 90:
                return (
                    "background-color: #fff2cc; color: #7f6000; font-weight:"
                    " bold;"
                )
            else:
                return (
                    "background-color: #f4cccc; color: #990000; font-weight:"
                    " bold;"
                )

        st.dataframe(
            df_ranking.style.map(
                color_semaforo, subset=["NIVEL DE ATENCION (%)"]
            ).format({"NIVEL DE ATENCION (%)": "{:.1f}%"}),
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("---")

        # =====================================================================
        # AUDITORÍA: DESGLOSE DE CARTERA
        # =====================================================================
        st.subheader("Auditoría: Desglose de Cartera")

        columnas_mostrar = [
            "AGENCIA",
            "ASESOR ASIGNADO",
            "FECHA SOLICITUD",
            "NOMBRE CLIENTE",
            "PRIMER FILTRO",
            "UNIDAD REAL DE INTERES",
            "ESTATUS PROSPECTO",
            "COMENTARIO ASESOR",
            "DIAS TRANSCURRIDOS SIN SEGUIMIENTO",
        ]

        condicion_atendido = df_validos_d["PRIMER FILTRO"] != ""
        condicion_vacio = df_validos_d["PRIMER FILTRO"] == ""

        estatus_activos_q = [
            "SEGUIMIENTO",
            "COTIZADO",
            "FINANCIAMIENTO",
            "FACTURADO",
            "CIERRE DE VENTA",
        ]
        estatus_perdidos_q = ["VENTA PERDIDA", "COMPRA CANCELADA"]
        estatus_perdidos_l = [
            "YA NO TIENE INTERES",
            "YA NO TIENE INTERÉS",
            "ERROR DE CAPTURA",
        ]

        df_activa = df_validos_d[
            condicion_atendido
            & (
                (df_validos_d["ESTATUS PROSPECTO"].isin(estatus_activos_q))
                | (
                    (df_validos_d["ESTATUS PROSPECTO"] == "")
                    & (df_validos_d["PRIMER FILTRO"] == "PROSPECTO CON INTERES")
                )
            )
        ]

        df_sin_atender = df_validos_d[condicion_vacio]

        df_perdida = df_validos_d[
            condicion_atendido
            & (
                (df_validos_d["PRIMER FILTRO"].isin(estatus_perdidos_l))
                | (df_validos_d["ESTATUS PROSPECTO"].isin(estatus_perdidos_q))
            )
        ]

        st.markdown("##### 🟢 Detalle de Cartera Activa")
        st.caption(
            "Prospectos atendidos que se mantienen con interés, en seguimiento,"
            " cotización, financiamiento o venta cerrada."
        )
        st.dataframe(
            df_activa[columnas_mostrar],
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("##### 🔴 Cartera Sin Atender")
        st.caption(
            "Prospectos asignados donde el vendedor AÚN NO captura el Primer"
            " Filtro."
        )
        st.dataframe(
            df_sin_atender[columnas_mostrar],
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("##### 🟠 Cartera Perdida")
        st.caption(
            "Prospectos descartados por falta de interés, error de captura,"
            " compra cancelada o venta perdida."
        )
        st.dataframe(
            df_perdida[columnas_mostrar],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.warning("Ajusta los filtros para ver el rendimiento.")
