import pandas as pd
import requests
import streamlit as st

# 1. Coloca aquí el ID de tu formulario de Kobo (ej. aX9z8Y7w6V5)
ASSET_ID = "COLOCA_AQUI_EL_ID_DE_TU_FORMULARIO"

# Endpoint para el servidor europeo / global
KOBO_URL = f"https://kf.kobotoolbox.org/api/v2/assets/{ASSET_ID}/data.json"

# Tu API Token integrado
HEADERS = {
    "Authorization": "Token a18c017a2e697f4ea1272375dae261ccec6b19d7"
}


@st.cache_data(ttl=600)  # Consulta y actualiza los datos cada 10 minutos
def cargar_datos_kobo():
    response = requests.get(KOBO_URL, headers=HEADERS)
    if response.status_code == 200:
        data = response.json()["results"]
        return pd.DataFrame(data)
    else:
        st.error(
            f"Error al conectar con KoboToolbox. Código de respuesta: {response.status_code}"
        )
        return pd.DataFrame()


# Carga del dataframe
df = cargar_datos_kobo()

# Mostrar datos en Streamlit
if not df.empty:
    st.success(f"Datos cargados exitosamente: {len(df)} registros.")
    st.dataframe(df)
