# ## ¿POR QUÉ SE PIERDE? ##

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import procesamiento as pr
from comun import (cargarResultados, encabezado, cifras, caja, estiloGrafico, numero, colorTipo, colorGrupo,
                   coral, verde, ambar, grisCalido, carbon)

exploratorio, modelado = cargarResultados()
m = modelado
baseModelo = pr.traducir(m["baseModelo"])

encabezado("", "¿Por qué se pierde?",
           f"{len(baseModelo)} combinaciones país-producto · mediana 2010–2023")

# Hallazgos principales del modelado, en cifras
orPerecedero = m["tablaOR"].loc["Perecedero", "OR"]
criticosCalidad = m["criticosCalidad"]
grupoAlto = m["perfilGrupos"].loc["Pérdida alta"]
grupoExport = m["perfilGrupos"].loc["Exportadores"]
cifras([
    ("Perecedero vs grano", f"{numero(orPerecedero, 0)}× más", "probabilidad (odds) de ser punto crítico", coral),
    ("Exportadores vs pérdida alta", f"{numero(grupoExport['TasaPerdida'] / grupoAlto['TasaPerdida'] * 100, 0)}%",
     "de la tasa: pierden casi la mitad", verde),
    ("Críticos con dato estimado", f"{numero(criticosCalidad['Estimado'], 0)}%",
     f"frente a {numero(criticosCalidad['Imputado'], 0)}% con dato imputado", ambar),
    ("Rendimiento y pérdida", "Relación débil", "solo el banano muestra relación (Spearman −0,61)", "#8A8F87"),
])

izquierda, derecha = st.columns(2)

# Tasa por producto (perecederos vs granos)
with izquierda:
    with caja("Los perecederos pierden más", "tasa de pérdida mediana por producto (%)"):
        perdidasProducto = pr.traducir(exploratorio["basePerdidas"])
        perecederosEs = [pr.productosEspanol[p] for p in pr.perecederos]
        porProducto = perdidasProducto.groupby("Producto")["TasaPerdida"].median().sort_values().reset_index()
        porProducto["Tipo"] = porProducto["Producto"].isin(perecederosEs).map({True: "Perecedero", False: "Grano"})
        fig = px.bar(porProducto, x="TasaPerdida", y="Producto", orientation="h", color="Tipo",
                     color_discrete_map=colorTipo, text="TasaPerdida", labels={"TasaPerdida": "", "Producto": ""})
        fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside", marker_cornerradius=4,
                          hovertemplate="%{y}: %{x:.1f}%<extra></extra>")
        fig.update_yaxes(categoryorder="array", categoryarray=porProducto["Producto"].tolist())
        fig.update_xaxes(range=[0, porProducto["TasaPerdida"].max() * 1.2], showticklabels=False)
        st.plotly_chart(estiloGrafico(fig, 420), width="stretch", theme=None)

# Probabilidad de ser crítico según el modelo
with derecha:
    with caja("Probabilidad de ser punto crítico", "según el tipo de producto y el origen del dato (regresión logística)"):
        escenarios = m["escenarios"].copy()
        escenarios["Tipo"] = escenarios["Perecedero"].map({1: "Perecedero", 0: "Grano"})
        escenarios["Dato"] = escenarios["DatoEstimado"].map({1: "Dato estimado", 0: "Dato imputado u oficial"})
        escenarios["Probabilidad"] = escenarios["Probabilidad"] * 100
        fig = px.bar(escenarios, x="Tipo", y="Probabilidad", color="Dato", barmode="group", text="Probabilidad",
                     color_discrete_map={"Dato estimado": carbon, "Dato imputado u oficial": "#C9C4B6"},
                     category_orders={"Tipo": ["Grano", "Perecedero"]}, labels={"Probabilidad": "", "Tipo": ""})
        fig.update_traces(texttemplate="%{text:.0f}%", textposition="outside", marker_cornerradius=4,
                          hovertemplate="%{x} · %{fullData.name}: %{y:.1f}%<extra></extra>")
        fig.update_yaxes(range=[0, 85], showticklabels=False, showgrid=False)
        st.plotly_chart(estiloGrafico(fig, 420), width="stretch", theme=None)

# Segmentos encontrados con K-means
st.markdown("#### Tres perfiles de país-producto")
roles = {"Pérdida alta": "Prioridad de intervención", "Exportadores": "Modelo a seguir", "Bajo volumen": "Bajo impacto"}
columnas = st.columns(3)
for col, grupo in zip(columnas, colorGrupo):
    fila = m["perfilGrupos"].loc[grupo]
    col.markdown(
        f"<div class='segmento' style='--acento:{colorGrupo[grupo]}'><div class='rol'>{roles[grupo]}</div>"
        f"<div class='titulo'>{grupo} · {int(fila['Combinaciones'])} combinaciones</div>"
        f"<div class='datos'>Tasa de pérdida: <b>{numero(fila['TasaPerdida'])}%</b> · "
        f"Pérdida: <b>US$ {numero(fila['PerdidaMillUSD'])} M</b> por combinación<br>"
        f"Perecederos: <b>{numero(fila['PctPerecederos'], 0)}%</b> · Críticos: <b>{numero(fila['PctCriticos'], 0)}%</b> · "
        f"Exportan: <b>{numero(fila['OrientacionExportadora'], 0)}%</b> de su oferta</div></div>",
        unsafe_allow_html=True)

izquierda, derecha = st.columns([1.35, 1])
with izquierda:
    with caja("Cada país-producto en su perfil", "eje horizontal: valor perdido · eje vertical: tasa de pérdida · ○ = punto crítico"):
        grupos = baseModelo.assign(Combinacion=lambda d: d["Pais"] + " · " + d["Producto"],
                                   PerdidaMill=lambda d: d["PerdidaUSD"] / 1e6)
        fig = px.scatter(grupos, x="PerdidaMill", y="TasaPerdida", color="NombreGrupo", color_discrete_map=colorGrupo,
                         category_orders={"NombreGrupo": list(colorGrupo)}, log_x=True, hover_name="Combinacion",
                         hover_data={"TasaPerdida": ":.1f", "PerdidaMill": ":.1f", "NombreGrupo": False},
                         labels={"PerdidaMill": "Valor perdido por año (millones de USD, escala log)",
                                 "TasaPerdida": "Tasa de pérdida (%)"})
        fig.update_traces(marker=dict(size=10, opacity=.85, line=dict(width=1, color="white")))
        criticos = grupos[grupos["Critico"] == 1]
        fig.add_trace(go.Scatter(x=criticos["PerdidaMill"], y=criticos["TasaPerdida"], mode="markers",
                                 name="Punto crítico", hoverinfo="skip",
                                 marker=dict(symbol="circle-open", size=16, color=carbon, line=dict(width=1.3))))
        fig.add_hline(y=10, line_dash="dot", line_color="#999")
        st.plotly_chart(estiloGrafico(fig, 460), width="stretch", theme=None)
with derecha:
    with caja("Qué distingue a cada perfil", "1 = el valor más alto entre perfiles"):
        indicadores = {"TasaPerdida": "Tasa de<br>pérdida", "PerdidaMillUSD": "Valor<br>perdido",
                       "IndiceRendimiento": "Rendimiento", "DependenciaImportadora": "Dependencia<br>importadora",
                       "OrientacionExportadora": "Orientación<br>exportadora", "PctPerecederos": "%<br>perecederos"}
        perfil = m["perfilGrupos"].loc[list(colorGrupo), list(indicadores)]
        radar = perfil / perfil.max()
        fig = go.Figure()
        for grupo, fila in radar.iterrows():
            etiquetas = list(indicadores.values())
            fig.add_trace(go.Scatterpolar(r=fila.tolist() + fila.tolist()[:1], theta=etiquetas + etiquetas[:1],
                                          name=grupo, fill="toself", opacity=.6,
                                          line=dict(color=colorGrupo[grupo], width=2),
                                          hovertemplate="%{theta}: %{r:.2f}<extra>" + grupo + "</extra>"))
        fig.update_layout(polar=dict(domain=dict(x=[0.16, 0.84], y=[0.04, 0.86]), bgcolor="white",
                                     radialaxis=dict(visible=True, range=[0, 1.05], showticklabels=False,
                                                     gridcolor="#efece4"),
                                     angularaxis=dict(tickfont=dict(size=11, color=grisCalido), rotation=90,
                                                      gridcolor="#efece4")))
        st.plotly_chart(estiloGrafico(fig, 460), width="stretch", theme=None)
