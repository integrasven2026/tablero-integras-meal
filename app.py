import streamlit as st
import pandas as pd
import plotly.express as px

# ---------------------------------------------------------
# CONFIGURACIÓN DE PÁGINA
# ---------------------------------------------------------
st.set_page_config(
    page_title="Consolidación Histórica de Participantes y Atenciones - COOPI Venezuela",
    layout="wide"
)

# ---------------------------------------------------------
# ENCABEZADO CON LOGO DE COOPI EN LA PARTE SUPERIOR DERECHA
# ---------------------------------------------------------
col_titulo, col_logo = st.columns([3, 1])

with col_titulo:
    st.title("Consolidación Histórica de Participantes y Atenciones - COOPI Venezuela")

with col_logo:
    st.image(
        "https://coopi.org/images/logo_coopi.png",
        width=220
    )

st.markdown("---")

# ---------------------------------------------------------
# CARGA DE ARCHIVOS DESDE LA BARRA LATERAL (UPLOADER)
# ---------------------------------------------------------
st.sidebar.header("Cargar Bases de Datos SIGA")
f1 = st.sidebar.file_uploader("1. Excel Agua Para La Vida", type=["xlsx"])
f2 = st.sidebar.file_uploader("2. Excel Eco Resiliencia", type=["xlsx"])

# ---------------------------------------------------------
# TRANSFORMACIÓN DE DATOS (ETL)
# ---------------------------------------------------------
@st.cache_data
def cargar_y_procesar_datos(f1_file, f2_file):
    # Proyecto 1: Agua Para La Vida
    df1_act = pd.read_excel(f1_file, sheet_name=0)
    df1_ben = pd.read_excel(f1_file, sheet_name='group_beneficiario')
    
    if '_submission_time' in df1_act.columns:
        df1_act['anio'] = pd.to_datetime(df1_act['_submission_time'], errors='coerce').dt.year
    elif 'today' in df1_act.columns:
        df1_act['anio'] = pd.to_datetime(df1_act['today'], errors='coerce').dt.year
    else:
        df1_act['anio'] = 2026

    m1 = df1_ben.merge(df1_act[['_index', 'Estado', 'Municipio', 'Parroquia', 'Actividad:', 'anio']], left_on='_parent_index', right_on='_index', how='left')

    df1_clean = pd.DataFrame({
        'proyecto': 'Agua Para La Vida',
        'socio': 'COOPI',
        'codigo_unico': m1['CodigoID'],
        'edad': m1['edad_anos'],
        'sexo': m1['Sexo'],
        'estado': m1['Estado'],
        'municipio': m1['Municipio'],
        'parroquia': m1['Parroquia'],
        'servicio_actividad': m1['Actividad:'],
        'anio': m1['anio'].fillna(2026).astype(int),
        'discapacidad': m1.get('discapacidad', pd.Series(['No']*len(m1))),
        'indigena': m1.get('indigena', pd.Series(['No']*len(m1))),
        'embarazada': m1.get('embarazada', pd.Series(['No']*len(m1)))
    })

    # Proyecto 2: Eco Resiliencia Costera
    df2_act = pd.read_excel(f2_file, sheet_name=0)
    df2_ben = pd.read_excel(f2_file, sheet_name='group_beneficiario')

    if '_submission_time' in df2_act.columns:
        df2_act['anio'] = pd.to_datetime(df2_act['_submission_time'], errors='coerce').dt.year
    elif 'today' in df2_act.columns:
        df2_act['anio'] = pd.to_datetime(df2_act['today'], errors='coerce').dt.year
    else:
        df2_act['anio'] = 2026

    m2 = df2_ben.merge(df2_act[['_index', 'Estado', 'Municipio', 'Parroquia', 'Actividad:', 'anio']], left_on='_parent_index', right_on='_index', how='left')

    df2_clean = pd.DataFrame({
        'proyecto': 'Eco Resiliencia Costera',
        'socio': 'COOPI',
        'codigo_unico': m2['CodigoID'],
        'edad': m2['Edad'],
        'sexo': m2['Sexo'],
        'estado': m2['Estado'],
        'municipio': m2['Municipio'],
        'parroquia': m2['Parroquia'],
        'servicio_actividad': m2['Actividad:'],
        'anio': m2['anio'].fillna(2026).astype(int),
        'discapacidad': m2.get('discapacidad', pd.Series(['No']*len(m2))),
        'indigena': m2.get('indigena', pd.Series(['No']*len(m2))),
        'embarazada': m2.get('embarazada', pd.Series(['No']*len(m2)))
    })

    base = pd.concat([df1_clean, df2_clean], ignore_index=True)

    base['sexo_std'] = base['sexo'].astype(str).str.strip().str.capitalize()
    base['estado_std'] = base['estado'].replace({'VE19': 'Sucre', 'SUCRE': 'Sucre'})
    base['municipio_std'] = base['municipio'].replace({'VE1914': 'Mariño', 'VE1906': 'Bermúdez', 'VE1911': 'Sucre'})

    base['edad_num'] = pd.to_numeric(base['edad'], errors='coerce')
    bins = [-1, 17, 49, 150]
    labels = ['0-17 años', '18-49 años', '50+ años']
    base['rango_etario'] = pd.cut(base['edad_num'], bins=bins, labels=labels)

    def clasificar_sector(actividad):
        act = str(actividad).lower()
        if any(k in act for k in ['agua', 'saneamiento', 'plomería', 'potabilización', 'hidrocaribe', 'a21', 'a24', 'a25', 'a14', 'a12', 'a11']):
            return 'Agua, Saneamiento e Higiene (WASH)'
        elif any(k in act for k in ['negocios', 'acuícola', 'turismo', 'capital semilla', 'a.3.2', 'medios de vida']):
            return 'Medios de Vida y Desarrollo Económico'
        elif any(k in act for k in ['residuos', 'reciclaje', 'desechos', 'basura', 'a34', 'a36', 'a33', 'a35', 'a31', 'a32']):
            return 'Gestión Ambiental y Residuos Sólidos'
        elif any(k in act for k in ['campaña', 'sensibilización', 'derechos', 'a22', 'a.2.2', 'oe1a1', 'a13']):
            return 'Protección y Sensibilización Comunitaria'
        else:
            return 'Otros / Servicios Generales'

    base['sector_servicio'] = base['servicio_actividad'].apply(clasificar_sector)

    coordenadas = {
        'Mariño': {'lat': 10.5694, 'lon': -62.5833},
        'Bermúdez': {'lat': 10.6667, 'lon': -63.2500},
        'Sucre': {'lat': 10.4500, 'lon': -64.1667},
        'Mejía': {'lat': 10.5000, 'lon': -63.8333},
        'Bolívar': {'lat': 10.4167, 'lon': -63.9833}
    }

    base['lat'] = base['municipio_std'].map(lambda x: coordenadas.get(x, {}).get('lat', 10.5000))
    base['lon'] = base['municipio_std'].map(lambda x: coordenadas.get(x, {}).get('lon', -63.5000))

    return base

# VERIFICACIÓN DE ARCHIVOS CARGADOS
if f1 is not None and f2 is not None:
    base_data = cargar_y_procesar_datos(f1, f2)

    # ---------------------------------------------------------
    # FILTROS LATERALES
    # ---------------------------------------------------------
    st.sidebar.markdown("---")
    st.sidebar.header("Filtros de Navegación")

    filtro_proyecto = st.sidebar.multiselect("Proyecto:", options=sorted(base_data['proyecto'].unique()), default=sorted(base_data['proyecto'].unique()))
    filtro_anio = st.sidebar.multiselect("Año:", options=sorted(base_data['anio'].unique()), default=sorted(base_data['anio'].unique()))
    filtro_estado = st.sidebar.multiselect("Estado:", options=sorted(base_data['estado_std'].unique()), default=sorted(base_data['estado_std'].unique()))
    filtro_municipio = st.sidebar.multiselect("Municipio:", options=sorted(base_data['municipio_std'].unique()), default=sorted(base_data['municipio_std'].unique()))
    filtro_sector = st.sidebar.multiselect("Sector MEAL:", options=sorted(base_data['sector_servicio'].unique()), default=sorted(base_data['sector_servicio'].unique()))

    # Filtrado dinámico
    df_filtrado = base_data[
        (base_data['proyecto'].isin(filtro_proyecto)) &
        (base_data['anio'].isin(filtro_anio)) &
        (base_data['estado_std'].isin(filtro_estado)) &
        (base_data['municipio_std'].isin(filtro_municipio)) &
        (base_data['sector_servicio'].isin(filtro_sector))
    ]

    df_unicos = df_filtrado.drop_duplicates(subset=['codigo_unico'], keep='first')
    total_u = max(len(df_unicos), 1)

    # ---------------------------------------------------------
    # MÉTRICAS GENERALES DE ATENCIÓN Y ALCANCE
    # ---------------------------------------------------------
    st.subheader("General de Atenciones y Cobertura")
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Total Atenciones", f"{len(df_filtrado):,}")
    m2.metric("Participantes Únicos", f"{len(df_unicos):,}")
    m3.metric("Estados Atendidos", f"{df_filtrado['estado_std'].nunique()}")
    m4.metric("Municipios Atendidos", f"{df_filtrado['municipio_std'].nunique()}")
    m5.metric("Sectores MEAL", f"{df_filtrado['sector_servicio'].nunique()}")

    st.markdown("---")

    # ---------------------------------------------------------
    # MÉTRICAS EN PORCENTAJE (DEMOGRAFÍA Y VULNERABILIDAD)
    # ---------------------------------------------------------
    st.subheader("Distribución de Participantes por Grupos de Vulnerabilidad (%)")
    
    pct_mujeres = (len(df_unicos[df_unicos['sexo_std'] == 'Mujer']) / total_u) * 100
    pct_hombres = (len(df_unicos[df_unicos['sexo_std'] == 'Hombre']) / total_u) * 100
    pct_ninos = (len(df_unicos[df_unicos['rango_etario'] == '0-17 años']) / total_u) * 100
    
    pct_disc = (len(df_unicos[df_unicos['discapacidad'].astype(str).str.lower().isin(['si', 'sí', 'true', '1'])]) / total_u) * 100
    pct_indigena = (len(df_unicos[df_unicos['indigena'].astype(str).str.lower().isin(['si', 'sí', 'true', '1'])]) / total_u) * 100
    pct_emb = (len(df_unicos[df_unicos['embarazada'].astype(str).str.lower().isin(['si', 'sí', 'true', '1'])]) / total_u) * 100

    v1, v2, v3, v4, v5, v6 = st.columns(6)
    v1.metric("% Mujeres", f"{pct_mujeres:.1f}%")
    v2.metric("% Hombres", f"{pct_hombres:.1f}%")
    v3.metric("% Niñas y Niños", f"{pct_ninos:.1f}%")
    v4.metric("% Discapacidad", f"{pct_disc:.1f}%")
    v5.metric("% Indígenas", f"{pct_indigena:.1f}%")
    v6.metric("% Embarazadas/Lact.", f"{pct_emb:.1f}%")

    st.markdown("---")

    # ---------------------------------------------------------
    # GRÁFICOS CON VALOR + PORCENTAJE EN LAS BARRAS
    # ---------------------------------------------------------
    col_g1, col_g2 = st.columns(2)

    with col_g1:
        st.subheader("Desglose por Sexo y Rango Etario (Únicos)")
        
        df_demo = df_unicos.groupby(['rango_etario', 'sexo_std'], observed=False).size().reset_index(name='count')
        df_demo['porcentaje'] = (df_demo['count'] / total_u) * 100
        df_demo['etiqueta'] = df_demo.apply(lambda r: f"{r['count']:,} ({r['porcentaje']:.1f}%)" if r['count'] > 0 else "", axis=1)

        fig_demo = px.bar(
            df_demo, 
            x="rango_etario", 
            y="count",
            color="sexo_std", 
            barmode="group",
            text="etiqueta",
            labels={"rango_etario": "Rango de Edad", "sexo_std": "Sexo", "count": "Cantidad"},
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        fig_demo.update_traces(textposition='outside')
        st.plotly_chart(fig_demo, width="stretch")

    with col_g2:
        st.subheader("Participantes por Sector de Respuesta MEAL")
        df_sectores = df_unicos['sector_servicio'].value_counts().reset_index()
        fig_sector = px.pie(
            df_sectores, 
            values='count', 
            names='sector_servicio', 
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig_sector.update_traces(textinfo='percent+value')
        st.plotly_chart(fig_sector, width="stretch")

    st.markdown("---")

    # ---------------------------------------------------------
    # MAPA Y COBERTURA POR ESTADO Y MUNICIPIO
    # ---------------------------------------------------------
    col_m1, col_m2 = st.columns(2)

    with col_m1:
        st.subheader("Ubicación Geográfica en Venezuela (Municipios)")
        df_mapa = df_unicos.groupby(['municipio_std', 'lat', 'lon']).size().reset_index(name='participantes')
        
        fig_map = px.scatter_mapbox(
            df_mapa,
            lat="lat",
            lon="lon",
            size="participantes",
            color="participantes",
            hover_name="municipio_std",
            hover_data={"lat": False, "lon": False, "participantes": True},
            color_continuous_scale=px.colors.cyclical.IceFire,
            size_max=35,
            zoom=7.8,
            center={"lat": 10.5000, "lon": -63.5000},
            mapbox_style="carto-positron"
        )
        fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
        st.plotly_chart(fig_map, width="stretch")

    with col_m2:
        st.subheader("Alcance por Estado")
        df_est = df_unicos['estado_std'].value_counts().reset_index()
        df_est['porcentaje'] = (df_est['count'] / total_u) * 100
        df_est['etiqueta'] = df_est.apply(lambda r: f"{r['count']:,} ({r['porcentaje']:.1f}%)", axis=1)

        fig_est = px.bar(
            df_est,
            x="count", 
            y="estado_std", 
            orientation="h",
            text="etiqueta",
            labels={"estado_std": "Estado", "count": "Cantidad"},
            color_discrete_sequence=['#27AE60']
        )
        fig_est.update_traces(textposition='outside')
        st.plotly_chart(fig_est, width="stretch")

    st.markdown("---")

    st.subheader("Alcance por Municipio")
    df_mun = df_unicos['municipio_std'].value_counts().reset_index()
    df_mun['porcentaje'] = (df_mun['count'] / total_u) * 100
    df_mun['etiqueta'] = df_mun.apply(lambda r: f"{r['count']:,} ({r['porcentaje']:.1f}%)", axis=1)

    fig_mun = px.bar(
        df_mun,
        x="count", 
        y="municipio_std", 
        orientation="h",
        text="etiqueta",
        labels={"municipio_std": "Municipio", "count": "Cantidad"},
        color_discrete_sequence=['#2E86C1']
    )
    fig_mun.update_traces(textposition='outside')
    st.plotly_chart(fig_mun, width="stretch")

    st.markdown("---")

    # ---------------------------------------------------------
    # TABLA BASE ANÓNIMA
    # ---------------------------------------------------------
    st.subheader("Base de Datos Anónima (Solo Código Único)")
    st.dataframe(
        df_unicos[['codigo_unico', 'sexo_std', 'edad_num', 'rango_etario', 'estado_std', 'municipio_std', 'parroquia', 'sector_servicio', 'proyecto', 'anio']],
        width="stretch"
    )

    csv = df_unicos[['codigo_unico', 'sexo_std', 'edad_num', 'rango_etario', 'estado_std', 'municipio_std', 'parroquia', 'sector_servicio', 'proyecto', 'anio']].to_csv(index=False).encode('utf-8')

    st.download_button(
        label="Descargar Base Anónima de Participantes Únicos (CSV)",
        data=csv,
        file_name="Participantes_Unicos_COOPI_Venezuela.csv",
        mime="text/csv"
    )
else:
    st.info("Por favor, carga los dos archivos Excel de SIGA en el menú lateral para desplegar los indicadores del tablero.")
