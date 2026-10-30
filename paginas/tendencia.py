# ## ¿HACIA DÓNDE VAMOS? ##

import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import procesamiento as pr
from comun import (cargarResultados, encabezado, cifras, caja, estiloGrafico, numero, coral, verde, ambar,
                   grisCalido, carbon)

exploratorio, modelado = cargarResultados()
m = modelado

encabezado("Paso 3 · Proyectar", "¿Hacia dónde vamos?", "tasa de pérdida regional 2010–2023 y meta ODS 12.3 a 2030")

# Cifras de la tendencia
serieSinSoya, rSinSoya = m["serieSinSoya"], m["rSinSoya"]
cifras([
    ("Tasa regional 2015", f"{numero(serieSinSoya.loc[2015], 2)}%", "punto de partida de la meta", grisCalido),
    ("Tasa regional 2023", f"{numero(serieSinSoya.loc[2023], 2)}%", "sin soya", ambar),
    ("Proyección 2030", f"{numero(m['proyeccion2030'])}%", f"al ritmo actual ({numero(rSinSoya.slope, 2)} p.p. por año)", coral),
    ("Meta ODS 12.3", f"{numero(m['meta2030'])}%", "reducir a la mitad la pérdida de 2015", verde),
])

# Serie regional, recta y meta
with caja("Al ritmo actual, la región no llega a la meta de 2030",
          "tasa de pérdida regional sin soya (la soya cambió su forma de reporte en 2019)"):
    aniosRecta = np.arange(2010, 2031)
    recta = rSinSoya.intercept + rSinSoya.slope * aniosRecta
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=aniosRecta, y=np.full(len(aniosRecta), m["meta2030"]), mode="lines", name="Meta ODS 12.3",
                             line=dict(color=verde, width=2, dash="dot"), hovertemplate="Meta: %{y:.1f}%<extra></extra>"))
    fig.add_trace(go.Scatter(x=aniosRecta[aniosRecta >= 2023], y=recta[aniosRecta >= 2023], mode="lines",
                             name="Proyección", line=dict(color=coral, width=2, dash="dash"),
                             hovertemplate="%{x}: %{y:.2f}%<extra>Proyección</extra>"))
    fig.add_trace(go.Scatter(x=serieSinSoya.index, y=serieSinSoya.values, mode="lines+markers", name="Tasa regional",
                             line=dict(color=carbon, width=2.5), marker=dict(size=7),
                             hovertemplate="%{x}: %{y:.2f}%<extra>Tasa regional</extra>"))
    fig.add_annotation(x=2030, y=m["proyeccion2030"], text=f"<b>{numero(m['proyeccion2030'])}%</b>", showarrow=False,
                       yshift=14, font=dict(color=coral, size=14))
    fig.add_annotation(x=2030, y=m["meta2030"], text=f"<b>{numero(m['meta2030'])}%</b>", showarrow=False,
                       yshift=-14, font=dict(color=verde, size=14))
    fig.update_layout(yaxis=dict(range=[0, 9], title="Tasa de pérdida (%)"), xaxis=dict(dtick=2))
    st.plotly_chart(estiloGrafico(fig, 430), width="stretch")

# Cambio anual por producto
with caja("Qué productos mejoran y cuáles empeoran", "cambio de la tasa regional por año (puntos porcentuales) · solo tendencias significativas"):
    tendencia = pr.traducir(m["tendenciaProducto"])
    tendencia = tendencia[(tendencia["Tendencia"] != "Sin tendencia") & (tendencia["Producto"] != "Soya")]
    tendencia = tendencia.sort_values("Pendiente (p.p./año)")
    colores = [coral if v > 0 else verde for v in tendencia["Pendiente (p.p./año)"]]
    fig = px.bar(tendencia, x="Pendiente (p.p./año)", y="Producto", orientation="h", text="Pendiente (p.p./año)",
                 labels={"Pendiente (p.p./año)": "", "Producto": ""})
    fig.update_traces(marker_color=colores, marker_cornerradius=4, texttemplate="%{text:+.3f}",
                      textposition="outside", hovertemplate="%{y}: %{x:+.3f} p.p./año<extra></extra>")
    fig.update_xaxes(range=[-0.22, 0.1], zeroline=True, zerolinecolor="#999", showticklabels=False)
    st.plotly_chart(estiloGrafico(fig, 360), width="stretch")
