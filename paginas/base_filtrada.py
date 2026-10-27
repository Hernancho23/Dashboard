# ## BASE FILTRADA ##

import streamlit as st

import procesamiento as pr
from comun import cargarResultados, basesFiltradas, resumenFiltros, caja, nota

exploratorio, modelado = cargarResultados()
perdidasF, maestraF = basesFiltradas()

st.title("Base filtrada")
st.caption(resumenFiltros())
nota("Las bases salen de FAOSTAT, se limpiaron en Power Query (7 columnas, nombres en español) "
     "y se procesan con el mismo código del notebook. Aquí se pueden ver y descargar con los filtros aplicados.")


def mostrarBase(titulo, df, archivo):
    # Tabla con buscador y botón de descarga en CSV
    with caja(f"{titulo} · {len(df)} filas"):
        st.dataframe(df, width="stretch", hide_index=True, height=320)
        st.download_button("Descargar CSV", df.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"),
                           file_name=archivo, mime="text/csv", key=archivo)


mostrarBase("Base de pérdidas (KPIs físicos)", perdidasF.drop(columns=["LimiteSuperior"]), "base_perdidas.csv")
mostrarBase("Base maestra (unión de las 4 bases)", maestraF, "base_maestra.csv")
mostrarBase("Base de modelado (país-producto, mediana 2010–2023, sin filtros)",
            pr.traducir(modelado["baseModelo"]), "base_modelado.csv")

# Resumen de las bases originales
with caja("Bases originales de FAOSTAT"):
    resumen = [{"Base": nombre, "Registros": len(df), "Países": df["Pais"].nunique(),
                "Productos": df["Producto"].nunique(), "Años": f"{df['Año'].min()}–{df['Año'].max()}"}
               for nombre, df in exploratorio["bases"].items()]
    st.dataframe(resumen, width="stretch", hide_index=True)
