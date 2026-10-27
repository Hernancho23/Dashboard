# ## DASHBOARD: DETECCIÓN DE PUNTOS CRÍTICOS DE PÉRDIDA DE ALIMENTOS ##
# Para correrlo:  streamlit run app.py

import streamlit as st

from comun import cargarResultados, estilosPagina, filtrosLaterales

# Configuración general de la página
st.set_page_config(page_title="Pérdida de alimentos AL", page_icon="🌽", layout="wide")
estilosPagina()

# Menú de páginas (como el ejemplo del profe: una sección por tema)
paginas = st.navigation({
    "Proyecto": [
        st.Page("paginas/resumen.py", title="Resumen", icon="📌", default=True),
    ],
    "Análisis exploratorio": [
        st.Page("paginas/puntos_criticos.py", title="Puntos críticos", icon="🔥"),
        st.Page("paginas/productos.py", title="Productos y tendencias", icon="🥑"),
        st.Page("paginas/paises.py", title="Países y KPIs", icon="🌎"),
    ],
    "Análisis avanzados": [
        st.Page("paginas/modelado.py", title="Modelado multivariado", icon="🧮"),
        st.Page("paginas/burbujas.py", title="Diagrama de burbujas", icon="🫧"),
    ],
    "Datos": [
        st.Page("paginas/descriptiva.py", title="Estadística descriptiva", icon="📋"),
        st.Page("paginas/base_filtrada.py", title="Base filtrada", icon="🗂️"),
    ],
})

# Filtros consultables en la barra lateral (aplican a todas las páginas)
exploratorio, modelado = cargarResultados()
filtrosLaterales(exploratorio)

st.sidebar.caption("Proyecto 7 · Minería de Datos · ITM\n\n"
                   "Jimena Cardona, Hernán Céspedes y Valentina Ramírez\n\n"
                   "Fuente: FAOSTAT (SUA, Producción, Precios al productor y Comercio).")

paginas.run()
