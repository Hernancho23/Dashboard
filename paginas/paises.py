# ## PAÍSES Y KPIs ##

import pandas as pd
import plotly.express as px
import streamlit as st

import procesamiento as pr
from comun import (basesFiltradas, resumenFiltros, sinDatos, caja, estiloGrafico, nota, numero,
                   rojo, verdeOscuro)

perdidasF, maestraF = basesFiltradas()
sinDatos(perdidasF)

st.title("Países y KPIs")
st.caption(resumenFiltros())
kpis = pr.kpisPorPais(perdidasF, maestraF).reset_index()

izquierda, derecha = st.columns(2)

# Pérdida económica por país
with izquierda:
    with caja("Pérdida económica acumulada por país"):
        perdidaPais = kpis.sort_values("PerdidaUSD")
        fig = px.bar(perdidaPais, x=perdidaPais["PerdidaUSD"] / 1e9, y="Pais", orientation="h",
                     color_discrete_sequence=[rojo], labels={"x": "Miles de millones de USD", "Pais": ""})
        fig.update_traces(hovertemplate="%{y}: %{x:.2f} mil mill. USD<extra></extra>", marker_cornerradius=4)
        st.plotly_chart(estiloGrafico(fig, 110 + 24 * len(perdidaPais)), width="stretch")
        nota("Refleja sobre todo el tamaño de la producción: Brasil no tiene la tasa más alta, pero es el mayor productor.")

# Tasa de pérdida por país
with derecha:
    with caja("Tasa de pérdida por país"):
        tasaPais = kpis.sort_values("TasaPerdida")
        fig = px.bar(tasaPais, x="TasaPerdida", y="Pais", orientation="h", color_discrete_sequence=[verdeOscuro],
                     labels={"TasaPerdida": "Tasa de pérdida (% de la oferta)", "Pais": ""})
        fig.update_traces(hovertemplate="%{y}: %{x:.1f}%<extra></extra>", marker_cornerradius=4)
        st.plotly_chart(estiloGrafico(fig, 110 + 24 * len(tasaPais)), width="stretch")
        nota("Mide la eficiencia: qué parte de la oferta se pierde. No sigue el mismo orden que la pérdida en dólares.")

# Tabla de los 6 KPIs
with caja("Los 6 KPIs por país"):
    tablaKpis = pd.DataFrame({
        "País": kpis["Pais"],
        "Pérdida total (t)": kpis["PerdidaTotal"].map(lambda v: numero(v, 0)),
        "Tasa de pérdida (%)": kpis["TasaPerdida"].map(numero),
        "Pérdida económica (mil mill. USD)": (kpis["PerdidaUSD"] / 1e9).map(lambda v: numero(v, 2)),
        "Índice de rendimiento": kpis["IndiceRendimiento"].map(numero),
        "Pérdida / exportaciones (%)": kpis["PerdidaSobreExport"].map(
            lambda v: "extremo" if pd.notna(v) and v > 1000 else ("—" if pd.isna(v) else numero(v))),
        "Dependencia importadora (%)": kpis["DependenciaImportadora"].map(numero),
        "_orden": kpis["TasaPerdida"]}).sort_values("_orden", ascending=False).drop(columns="_orden")
    st.dataframe(tablaKpis, width="stretch", hide_index=True)
    st.caption("Tasa = pérdida / (producción + importaciones). Índice de rendimiento: 100 = mediana regional. "
               "Venezuela sale como «extremo» en pérdida/exportaciones porque casi no exporta estos productos.")
