# ## DASHBOARD: DETECCIÓN DE PUNTOS CRÍTICOS DE PÉRDIDA DE ALIMENTOS ##
# Para correrlo:  streamlit run app.py

import streamlit as st

from comun import cargarResultados, estilosPagina, filtrosLaterales

# Configuración general de la página
st.set_page_config(page_title="Pérdida de alimentos · América Latina", page_icon="🌽", layout="wide")
estilosPagina()

# Menú: la historia en cuatro pasos, el explorador y la ficha técnica
paginas = st.navigation([
    st.Page("paginas/panorama.py", title="Panorama", icon="🌎", default=True),
    st.Page("paginas/donde.py", title="¿Dónde se pierde?", icon="📍"),
    st.Page("paginas/porque.py", title="¿Por qué se pierde?", icon="🔎"),
    st.Page("paginas/tendencia.py", title="¿Hacia dónde vamos?", icon="📈"),
    st.Page("paginas/explorador.py", title="Explorador de datos", icon="🗂️"),
    st.Page("paginas/ficha.py", title="Ficha técnica", icon="📐"),
])

# Filtros en la barra lateral
exploratorio, modelado = cargarResultados()
filtrosLaterales(exploratorio)
st.sidebar.caption("Jimena Cardona · Hernán Céspedes · Valentina Ramírez\n\nMinería de Datos · ITM · Fuente: FAOSTAT")

paginas.run()
