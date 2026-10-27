# ## ESTADÍSTICA DESCRIPTIVA ##

import pandas as pd
import streamlit as st

from comun import basesFiltradas, resumenFiltros, sinDatos, caja, nota, numero

perdidasF, maestraF = basesFiltradas()
sinDatos(perdidasF)

st.title("Estadística descriptiva")
st.caption(resumenFiltros())

# Variables numéricas de la base filtrada
variables = {
    "Pérdida (t)": perdidasF["Perdida"], "Oferta (t)": perdidasF["Oferta"],
    "Tasa de pérdida (%)": perdidasF["TasaPerdida"], "Dependencia importadora (%)": perdidasF["DependenciaImportadora"],
    "Índice de rendimiento": perdidasF["IndiceRendimiento"], "Precio al productor (USD/t)": maestraF["Precio_USD_ton"],
    "Pérdida económica (USD)": maestraF["PerdidaUSD"],
}

with caja("Medidas descriptivas"):
    filas = []
    for nombre, serie in variables.items():
        serie = serie.dropna()
        filas.append({"Variable": nombre, "n": len(serie), "Media": numero(serie.mean(), 1),
                      "Mediana": numero(serie.median(), 1), "Desv. estándar": numero(serie.std(), 1),
                      "Mínimo": numero(serie.min(), 1), "Q1": numero(serie.quantile(.25), 1),
                      "Q3": numero(serie.quantile(.75), 1), "Máximo": numero(serie.max(), 1),
                      "Asimetría": numero(serie.skew(), 2)})
    st.dataframe(pd.DataFrame(filas), width="stretch", hide_index=True)
    nota("En todas las variables la media es mayor que la mediana y la asimetría es positiva: pocos países grandes "
         "elevan el promedio. Por eso en el proyecto se usan la mediana y la correlación de Spearman.")

# Tasa de pérdida descrita por grupo
with caja("Tasa de pérdida por grupo"):
    agrupar = st.radio("Agrupar por", ["Producto", "Pais", "Tipo", "Calidad"], horizontal=True,
                       format_func=lambda v: {"Pais": "País", "Calidad": "Calidad del dato"}.get(v, v))
    resumen = (perdidasF.groupby(agrupar)["TasaPerdida"]
               .agg(n="count", Media="mean", Mediana="median", Desv="std", Mínimo="min", Máximo="max")
               .sort_values("Mediana", ascending=False).reset_index())
    for col in ["Media", "Mediana", "Desv", "Mínimo", "Máximo"]:
        resumen[col] = resumen[col].map(lambda v: numero(v, 1) if pd.notna(v) else "—")
    st.dataframe(resumen.rename(columns={"Desv": "Desv. estándar", "Pais": "País"}),
                 width="stretch", hide_index=True)
