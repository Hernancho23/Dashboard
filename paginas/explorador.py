# ## EXPLORADOR DE DATOS ##

import pandas as pd
import plotly.express as px
import streamlit as st

import procesamiento as pr
from comun import (basesFiltradas, sinDatos, textoFiltros, encabezado, caja, estiloGrafico, numero, coral)

perdidasF, maestraF = basesFiltradas()
sinDatos(perdidasF)

encabezado("", "Explorador de datos", textoFiltros())

# Evolución de la tasa de pérdida con los filtros
with caja("Evolución de la tasa de pérdida", "pérdida / oferta de la selección, por año (%)"):
    porAnio = perdidasF.groupby("Año")[["Perdida", "Oferta"]].sum()
    porAnio = (porAnio["Perdida"] / porAnio["Oferta"] * 100).rename("Tasa").reset_index()
    fig = px.area(porAnio, x="Año", y="Tasa", markers=True, color_discrete_sequence=[coral],
                  labels={"Tasa": "Tasa de pérdida (%)", "Año": ""})
    fig.update_traces(hovertemplate="%{x}: %{y:.2f}%<extra></extra>", line_width=2.5)
    fig.update_yaxes(rangemode="tozero")
    st.plotly_chart(estiloGrafico(fig, 340), width="stretch", theme=None)

# Indicadores por país de la selección
with caja("Indicadores por país", "acumulado de la selección"):
    kpis = pr.kpisPorPais(perdidasF, maestraF).reset_index()
    tabla = pd.DataFrame({
        "País": kpis["Pais"],
        "Pérdida (t)": kpis["PerdidaTotal"].map(lambda v: numero(v, 0)),
        "Tasa de pérdida (%)": kpis["TasaPerdida"].map(numero),
        "Valor perdido (mil mill. USD)": (kpis["PerdidaUSD"] / 1e9).map(lambda v: numero(v, 2)),
        "Índice de rendimiento": kpis["IndiceRendimiento"].map(numero),
        "Pérdida / exportaciones (%)": kpis["PerdidaSobreExport"].map(
            lambda v: "muy alto" if pd.notna(v) and v > 1000 else ("—" if pd.isna(v) else numero(v))),
        "Dependencia importadora (%)": kpis["DependenciaImportadora"].map(numero),
        "_orden": kpis["TasaPerdida"]}).sort_values("_orden", ascending=False).drop(columns="_orden")
    st.table(tabla.set_index("País").rename_axis(None))

# Datos para descargar
with caja("Datos de la selección", "país · producto · año"):
    columnas = {"Pais": "País", "Producto": "Producto", "Tipo": "Tipo", "Año": "Año", "Perdida": "Pérdida (t)",
                "Oferta": "Oferta (t)", "TasaPerdida": "Tasa de pérdida (%)",
                "DependenciaImportadora": "Dependencia importadora (%)", "IndiceRendimiento": "Índice de rendimiento",
                "Calidad": "Origen del dato"}
    datos = perdidasF[list(columnas)].rename(columns=columnas).round(2)
    # Colores fijos de la tabla para que se vea igual con cualquier tema del navegador
    st.dataframe(datos.style.format(precision=2, decimal=",", thousands=".")
                 .set_properties(**{"background-color": "white", "color": "#23302A"}),
                 width="stretch", hide_index=True, height=320)
    st.download_button("Descargar CSV", datos.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"),
                       file_name="perdida_alimentos_seleccion.csv", mime="text/csv")
