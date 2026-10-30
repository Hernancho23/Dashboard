# ## PANORAMA ##

import plotly.express as px
import streamlit as st

import procesamiento as pr
from comun import (cargarResultados, basesFiltradas, sinDatos, textoFiltros, cifras, caja, estiloGrafico, numero,
                   codigosISO, escalaPerdida, coral, verde, ambar, bosque, bosqueClaro, grisCalido)

exploratorio, modelado = cargarResultados()
perdidasF, maestraF = basesFiltradas()
sinDatos(perdidasF)

# Portada con la cifra principal
valorPerdido = maestraF["PerdidaUSD"].sum() / 1e9
st.markdown(
    f"<div class='portada'><div class='etiqueta'>Pérdida de alimentos · América Latina · {textoFiltros()}</div>"
    f"<h1>US$ {numero(valorPerdido)} mil millones en alimentos perdidos antes de llegar al mercado</h1>"
    f"<p>17 países · 10 productos · pérdidas en cosecha, poscosecha, almacenamiento y transporte (FAOSTAT)</p></div>",
    unsafe_allow_html=True)

# Cifras principales
tasa = perdidasF["Perdida"].sum() / perdidasF["Oferta"].sum() * 100
baseModelo = modelado["baseModelo"]
cifras([
    ("Toneladas perdidas", f"{numero(perdidasF['Perdida'].sum() / 1e6)} M t", "volumen acumulado", coral),
    ("Tasa de pérdida", f"{numero(tasa)}%", "de la oferta disponible", ambar),
    ("Puntos críticos", f"{baseModelo['Critico'].sum()} de {len(baseModelo)}", "país-producto con tasa ≥ 10%", coral),
    ("Meta ODS 12.3 a 2030", f"{numero(modelado['proyeccion2030'])}% vs {numero(modelado['meta2030'])}%",
     "proyección frente a la meta", verde),
])

# Mapa de la tasa de pérdida y valor perdido por país
kpis = pr.kpisPorPais(perdidasF, maestraF).reset_index()
kpis["CodigoISO"] = kpis["Pais"].map(codigosISO)
kpis["PerdidaMilMill"] = kpis["PerdidaUSD"] / 1e9

izquierda, derecha = st.columns([1.25, 1])
with izquierda:
    with caja("Tasa de pérdida por país", "% de la oferta que se pierde"):
        fig = px.choropleth(kpis, locations="CodigoISO", color="TasaPerdida", hover_name="Pais",
                            hover_data={"CodigoISO": False, "TasaPerdida": ":.1f", "PerdidaMilMill": ":.2f"},
                            color_continuous_scale=escalaPerdida,
                            labels={"TasaPerdida": "Tasa (%)", "PerdidaMilMill": "Pérdida (mil mill. USD)"})
        fig.update_geos(projection_type="mercator", lataxis_range=[-56, 33], lonaxis_range=[-118, -33],
                        showcountries=True, countrycolor="white", showframe=False, showcoastlines=False,
                        landcolor="#ECE8DD", showland=True, bgcolor="white")
        fig.update_traces(marker_line_color="white", marker_line_width=.8)
        fig.update_layout(coloraxis_colorbar=dict(title="%", thickness=12, len=.6), margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(estiloGrafico(fig, 560), width="stretch")
with derecha:
    with caja("Valor perdido por país", "miles de millones de USD, a precio al productor"):
        orden = kpis.sort_values("PerdidaMilMill")
        principal = orden.iloc[-1]
        colores = [coral if p == principal["Pais"] else "#C9C4B6" for p in orden["Pais"]]
        fig = px.bar(orden, x="PerdidaMilMill", y="Pais", orientation="h", text="PerdidaMilMill",
                     labels={"PerdidaMilMill": "", "Pais": ""})
        fig.update_traces(marker_color=colores, marker_cornerradius=4, texttemplate="%{text:.1f}",
                          textposition="outside", hovertemplate="%{y}: %{x:.2f} mil mill. USD<extra></extra>")
        fig.update_xaxes(showticklabels=False, range=[0, orden["PerdidaMilMill"].max() * 1.15])
        st.plotly_chart(estiloGrafico(fig, 560), width="stretch")
