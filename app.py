import pandas as pd
import requests
import streamlit as st

st.set_page_config(
    page_title="Tablero Integras MEAL", layout="wide"
)

# Configuración API Kobo (Servidor Europeo)
HEADERS = {
    "Authorization": "Token a18c017a2e697f4ea1272375dae261ccec6b19d7"
}

# IDs de los proyectos
PROYECTOS = {
    "Agua para la Vida": "agSTXreJaqyWNZCMkLBiAD",
    "Eco Resiliencia Costera": "aDT97q2nGcREipjSMeekrL",
}


@st.cache_data(ttl=600)  # Consulta Kobo cada 10 minutos
def cargar_proyecto_kobo(asset_id, nombre_proyecto):
    url = f"https://eu.kobotoolbox.org/api/v2/assets/{asset_id}/data.json"
    response = requests.get(url, headers=HEADERS)

    if response.status_code == 200:
        data = response.json().get("results", [])
        df = pd.DataFrame(data)
        if not df.empty:
            df["Proyecto"] = nombre_proyecto
        return df
    else:
        st.error(
            f"Error al cargar '{nombre_proyecto}'. Código: {response.status_code}"
        )
        return pd.DataFrame()


# Cargar y unir ambas bases de datos
df_agua = cargar_proyecto_kobo(
    PROYECTOS["Agua para la Vida"], "Agua para la Vida"
)
df_eco = cargar_proyecto_kobo(
    PROYECTOS["Eco Resiliencia Costera"], "Eco Resiliencia Costera"
)

# Consolidar ambas bases en un solo DataFrame
df_consolidado = pd.concat([df_agua, df_eco], ignore_index=True)

# Encabezado del Dashboard
st.title("tablero-integras-meal")
st.caption(
    "Reporte de participantes beneficiados por la implementación de Coopi en Venezuela"
)

# Visualización de métricas generales y tabla
if not df_consolidado.empty:
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Registros", len(df_consolidado))
    col2.metric("Agua para la Vida", len(df_agua))
    col3.metric("Eco Resiliencia Costera", len(df_eco))

    st.subheader("Base de Datos Consolidada (En Vivo)")
    st.dataframe(df_consolidado, use_container_width=True)
else:
    st.warning("No se pudieron consultar los datos desde KoboToolbox.")
